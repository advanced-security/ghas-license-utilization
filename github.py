import requests
import csv
import json
import os
import time
import threading
import concurrent.futures
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from models import Repository
from helpers import *

logger = get_logger()


CHECKPOINT_LOCK = threading.Lock()
MAX_WORKERS = 5

DEFAULT_SERVER_URL = "https://api.github.com"
REQUEST_TIMEOUT = 30  # seconds
MAX_RATE_LIMIT_RETRIES = 3
# The refs query only fetches branch tips, so it can use large pages cheaply
REFS_PAGE_SIZE = 100
# History pages start large and shrink automatically if GitHub times out (502/504) on a branch
HISTORY_PAGE_SIZE = 100
MIN_HISTORY_PAGE_SIZE = 10
# Log a progress line for a repository every this many requests, so long-running repositories don't look hung
PROGRESS_LOG_INTERVAL = 25


class GitHubAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class LoggingRetry(Retry):
    # urllib3 only logs retries at DEBUG level - surface them so slow requests are visible
    def increment(self, method=None, url=None, response=None, error=None, *args, **kwargs):
        new_retry = super().increment(method, url, response, error, *args, **kwargs)
        reason = f"HTTP {response.status}" if response is not None else repr(error)
        logger.warning(f"{method} {url} failed ({reason}); retrying ({new_retry.total} retries left)")
        return new_retry


@lru_cache(maxsize=None)
def get_session(token):
    # Retries transient server/gateway errors and connection failures with exponential backoff (2s, 4s, 8s).
    # Kept short because a repeated GraphQL 502/504 usually means the query is too big, which
    # get_active_committers_in_last_90_days handles by shrinking the page size instead.
    session = requests.Session()
    session.headers["Authorization"] = f"token {token}"
    retry = LoggingRetry(
        total=3,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],  # GraphQL uses POST
        respect_retry_after_header=True,
        raise_on_status=False,  # return the last response so callers can report it
    )
    # Pool sized for the worker threads sharing this session
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=MAX_WORKERS))
    return session


def get_graphql_url(server_url=DEFAULT_SERVER_URL):
    # GitHub.com serves GraphQL at https://api.github.com/graphql; GHES at https://HOSTNAME/api/graphql
    server_url = server_url.rstrip("/")
    if server_url == DEFAULT_SERVER_URL:
        return f"{server_url}/graphql"
    # Remove any /api/vX suffix to get the base URL (supports v3, v4, etc.)
    base_url = re.sub(r"/api/v\d+$", "", server_url)
    return f"{base_url}/api/graphql"


def github_request(method, url, token, **kwargs):
    # Send a request, sleeping and retrying when GitHub reports we are rate limited
    session = get_session(token)
    for _ in range(MAX_RATE_LIMIT_RETRIES + 1):
        response = session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
        if not handle_rate_limit(response):
            return response
    return response


def graphql_query(query, variables, token, headers=None, server_url=DEFAULT_SERVER_URL):
    response = github_request(
        "POST", get_graphql_url(server_url), token, json={"query": query, "variables": variables}, headers=headers
    )
    if response.status_code == 401:
        raise GitHubAPIError(
            f"401 Unauthorized: token is invalid for {server_url} or lacks required scopes", 401
        )
    if not response.ok:
        raise GitHubAPIError(f"HTTP {response.status_code}: {response.text[:200]}", response.status_code)
    try:
        data = response.json()
    except ValueError:
        raise GitHubAPIError(
            f"Non-JSON response (HTTP {response.status_code}): {response.text[:200]}", response.status_code
        )
    if data.get("errors"):
        raise GitHubAPIError(f"GraphQL errors: {data['errors']}", response.status_code)
    return data["data"]


def load_checkpoint(checkpoint):
    # Returns {"org/repo": [committers]} for repositories already fetched by a previous run
    results = {}
    if not checkpoint or not os.path.exists(checkpoint):
        return results
    with open(checkpoint, "r") as file:
        for line in file:
            try:
                entry = json.loads(line)
                results[entry["repo"]] = entry["active_committers"]
            except (ValueError, KeyError):
                continue  # e.g. a partially written last line from an interrupted run
    logger.info(f"Loaded active committers for {len(results)} repositories from checkpoint {checkpoint}")
    return results


def save_checkpoint(checkpoint, repo, active_committers):
    if not checkpoint:
        return
    with CHECKPOINT_LOCK, open(checkpoint, "a") as file:
        file.write(json.dumps({"repo": repo.get_full_name(), "active_committers": active_committers}) + "\n")


def add_active_committers_from_report(report, repositories):
    with open(report, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            user_login, org_repo, *_ = row
            org, repo_name = org_repo.split("/")

            if org is None or repo_name is None:
                return

            for repo in repositories:
                if repo.name == repo_name and repo.org == org:
                    repo.add_committer(user_login)


def add_active_committers_from_api(
    repositories, token, group=1, checkpoint=None, max_workers=MAX_WORKERS, server_url=DEFAULT_SERVER_URL
):
    logger.info(f"Fetching active committers from GitHub API...")
    completed = load_checkpoint(checkpoint)
    to_fetch = []
    for repo in repositories:
        if repo.get_full_name() in completed:
            repo.add_active_committers(completed[repo.get_full_name()])
        elif repo.get_visibility() == "public":
            # Public repositories don't consume GHAS licenses, so their committers aren't needed
            continue
        else:
            to_fetch.append(repo)
    logger.info(
        f"{len(repositories) - len(to_fetch)} repositories skipped (public or already in checkpoint), "
        f"{len(to_fetch)} to fetch using {max_workers} workers"
    )

    def fetch(repo):
        active_committers = get_active_committers_in_last_90_days(repo.org, repo.name, token, server_url)
        save_checkpoint(checkpoint, repo, active_committers)
        return active_committers

    failed = []
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch, repo): repo for repo in to_fetch}
        for i, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            repo = futures[future]
            elapsed = time.monotonic() - start
            try:
                active_committers = future.result()
                repo.add_active_committers(active_committers)
                logger.info(
                    f"[{group}:{i}/{len(to_fetch)}] Processed repository: {repo.get_full_name()} "
                    f"({len(active_committers)} active committers, {elapsed:.0f}s elapsed)"
                )
            except (GitHubAPIError, requests.RequestException) as e:
                if getattr(e, "status_code", None) == 401:
                    # Every remaining request would fail the same way - stop instead of flagging each repository.
                    # Repositories already fetched are in the checkpoint, so the run can be resumed.
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                logger.warning(
                    f"[{group}:{i}/{len(to_fetch)}] Failed to fetch active committers for {repo.get_full_name()}: {e}"
                )
                repo.committers_fetch_failed = True
                failed.append(repo.get_full_name())
    if failed:
        logger.warning(
            f"Could not fetch active committers for {len(failed)} repositories "
            f"(flagged as unknown in the report): {', '.join(failed)}"
        )


def add_active_committers(report, repositories, token, group=1, checkpoint=None, server_url=DEFAULT_SERVER_URL):
    try:
        add_active_committers_from_report(report, repositories)
    except (Exception, TypeError) as e:
        add_active_committers_from_api(repositories, token, group, checkpoint, server_url=server_url)


def get_organizations(args, token):
    orgs_in_ent = []
    if not args.enterprise:
        orgs_in_ent.append(args.organization)
    else:
        orgs_in_ent = get_orgs_in_ent(args.enterprise, token, args.server_url)
    return orgs_in_ent


def process_organizations(orgs_in_ent, token, args=None):
    server_url = getattr(args, "server_url", DEFAULT_SERVER_URL)
    include_inactive = getattr(args, "include_inactive", False)
    total_repositories = []
    for i, org in enumerate(orgs_in_ent, start=1):
        logger.info(f"[{i}/{len(orgs_in_ent)}] Processing organization: {org}")
        total_repositories.extend(get_ghas_status_for_repos(org, token, server_url, include_inactive))
    return total_repositories


def get_ghas_status_for_repos(org, token, server_url=DEFAULT_SERVER_URL, include_inactive=False):
    url = f"{server_url.rstrip('/')}/orgs/{org}/repos?per_page=100"
    page = 1
    repos = []

    while True:
        try:
            response = github_request("GET", url, token, params={"page": page})
        except requests.RequestException as e:
            logger.error(f"Request for {org} repositories (page {page}) failed: {e}")
            break

        if response.status_code == 401:
            raise GitHubAPIError(
                f"401 Unauthorized listing repositories for {org}: token is invalid for {server_url} "
                f"or lacks required scopes",
                401,
            )
        if response.ok:
            data = response.json()
            for repo_data in data:
                owner, name = repo_data["full_name"].split("/")
                ghas_status = (
                    repo_data.get("security_and_analysis", {})
                    .get("advanced_security", {})
                    .get("status", "")
                    == "enabled"
                )
                visibility = repo_data["visibility"]
                pushed_at = repo_data["pushed_at"]
                archived = repo_data["archived"]
                if not archived:
                    repo = Repository(name, owner, ghas_status, visibility, pushed_at)
                    repos.append(repo)
                elif include_inactive:
                    logger.info(f"Including archived repository: {owner}/{name}")
                    repo = Repository(name, owner, ghas_status, visibility, pushed_at)
                    repos.append(repo)
                else:
                    logger.info(f"Skipping archived repository: {owner}/{name}")
            if "next" not in response.links:
                break
            page += 1
        else:
            logger.error(
                f"Failed to list repositories for {org} from {server_url} (page {page}): "
                f"{response.status_code}:{response.text[:200]}. Results for this org are incomplete."
            )
            break
    return repos


# Lightweight: branch tips only, so stale and already-covered branches can be skipped without fetching history
BRANCHES_QUERY = """
query getBranches($org: String!, $repo: String!, $refsPageSize: Int!, $refsAfter: String) {
    repository(owner: $org, name: $repo) {
        visibility
        defaultBranchRef {
            name
        }
        refs(refPrefix: "refs/heads/", first: $refsPageSize, after: $refsAfter) {
            nodes {
                name
                target {
                    ... on Commit {
                        oid
                        committedDate
                    }
                }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}
"""

BRANCH_HISTORY_QUERY = """
query getBranchCommitters($org: String!, $repo: String!, $ref: String!, $since: GitTimestamp!, $historyPageSize: Int!, $historyAfter: String) {
    repository(owner: $org, name: $repo) {
        ref(qualifiedName: $ref) {
            target {
                ... on Commit {
                    history(first: $historyPageSize, since: $since, after: $historyAfter) {
                        nodes {
                            oid
                            author {
                                user {
                                    login
                                }
                            }
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
        }
    }
}
"""


def _parse_github_datetime(value):
    # GitHub returns e.g. "2026-10-19T12:34:56Z"; fromisoformat only accepts "Z" from Python 3.11
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _get_branches(org, repo, token, server_url=DEFAULT_SERVER_URL):
    # Returns (visibility, default branch name, [{"name", "oid", "committedDate"}])
    branches = []
    visibility = None
    default_branch = None
    refs_after = None
    while True:
        variables = {"org": org, "repo": repo, "refsPageSize": REFS_PAGE_SIZE, "refsAfter": refs_after}
        repository = graphql_query(BRANCHES_QUERY, variables, token, server_url=server_url).get("repository")
        if repository is None:
            raise GitHubAPIError(f"Repository {org}/{repo} not found or not accessible")

        visibility = repository.get("visibility")
        if visibility == "PUBLIC":
            return visibility, None, []
        default_branch = (repository.get("defaultBranchRef") or {}).get("name")

        refs = repository.get("refs") or {}
        for ref in refs.get("nodes") or []:
            target = ref.get("target") or {}
            if target.get("oid"):  # skip refs that don't point at a commit
                branches.append(
                    {"name": ref["name"], "oid": target["oid"], "committedDate": target.get("committedDate")}
                )

        page_info = refs.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            return visibility, default_branch, branches
        refs_after = page_info.get("endCursor")


def get_active_committers_in_last_90_days(org, repo, token, server_url=DEFAULT_SERVER_URL):
    # Raises GitHubAPIError / requests.RequestException if the repository can't be queried
    if org is None or repo is None:
        return list()

    full_name = f"{org}/{repo}"
    since_dt = datetime.now(timezone.utc) - timedelta(days=90)
    since = since_dt.isoformat()

    visibility, default_branch, branches = _get_branches(org, repo, token, server_url)
    if visibility == "PUBLIC":
        return list()

    # A branch whose tip is older than the window has no commits in it
    recent_branches = [
        b for b in branches if b["committedDate"] and _parse_github_datetime(b["committedDate"]) >= since_dt
    ]
    # Walk the default branch first: most branches share its history, so they can stop as soon as they reach it
    recent_branches.sort(key=lambda b: b["name"] != default_branch)

    active_committers = set()
    seen_commits = set()
    page_size = HISTORY_PAGE_SIZE
    requests_made = 0
    skipped = len(branches) - len(recent_branches)

    for branch_number, branch in enumerate(recent_branches, start=1):
        if branch["oid"] in seen_commits:
            # Tip already reached through another branch (e.g. merged), so its history is covered
            skipped += 1
            continue

        history_after = None
        while True:
            variables = {
                "org": org,
                "repo": repo,
                "ref": f"refs/heads/{branch['name']}",
                "since": since,
                "historyPageSize": page_size,
                "historyAfter": history_after,
            }
            try:
                data = graphql_query(BRANCH_HISTORY_QUERY, variables, token, server_url=server_url)
            except GitHubAPIError as e:
                # Repeated 502/504 means GitHub timed out on the query - retry the same page with a smaller one
                if e.status_code in (502, 504) and page_size > MIN_HISTORY_PAGE_SIZE:
                    page_size = max(page_size // 2, MIN_HISTORY_PAGE_SIZE)
                    logger.warning(f"{full_name}: GitHub timed out, reducing history page size to {page_size}")
                    continue
                raise

            requests_made += 1
            if requests_made % PROGRESS_LOG_INTERVAL == 0:
                logger.info(
                    f"{full_name}: still fetching - branch {branch_number}/{len(recent_branches)}, "
                    f"{requests_made} history requests, {len(active_committers)} committers so far"
                )

            ref = (data.get("repository") or {}).get("ref") or {}
            history = (ref.get("target") or {}).get("history")
            if not history:
                break  # branch deleted since it was listed

            nodes = history.get("nodes") or []
            # History is newest first. If this page ends on a commit an earlier branch already walked,
            # everything older on this branch was covered too.
            reached_seen_history = bool(nodes) and nodes[-1]["oid"] in seen_commits
            for commit in nodes:
                seen_commits.add(commit["oid"])
                user = (commit.get("author") or {}).get("user")
                if user:
                    active_committers.add(user["login"])

            page_info = history.get("pageInfo") or {}
            if reached_seen_history or not page_info.get("hasNextPage"):
                break
            history_after = page_info.get("endCursor")

    logger.debug(
        f"{full_name}: {len(active_committers)} committers from {len(branches) - skipped}/{len(branches)} branches "
        f"in {requests_made} history requests"
    )

    # Remove dependabot[bot] from active committers
    active_committers.discard("dependabot[bot]")

    return list(active_committers)


def get_orgs_in_ent(enterprise_name, token, server_url=DEFAULT_SERVER_URL):
    headers = {"X-Github-Next-Global-ID": "true"}
    orgs = []
    end_cursor = None
    while True:
        query = """
        query getOrgsInEnterprise($enterprise: String!, $after: String) {
            enterprise(slug: $enterprise) {
                organizations(first: 100, after: $after) {
                    nodes {
                        login
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {"enterprise": enterprise_name, "after": end_cursor}
        data = graphql_query(query, variables, token, headers=headers, server_url=server_url)
        logger.debug(json.dumps(data, indent=4))

        enterprise = data.get("enterprise")
        if enterprise is None:
            raise GitHubAPIError(f"Enterprise {enterprise_name} not found or not accessible")

        organizations = enterprise["organizations"]
        orgs += [org["login"] for org in organizations["nodes"] if org is not None]

        if organizations["pageInfo"]["hasNextPage"]:
            end_cursor = organizations["pageInfo"]["endCursor"]
        else:
            break
    return orgs


def handle_rate_limit(response):
    # Check the rate limit. Safe to call from multiple threads.
    # Returns True if the request was rate limited (after sleeping) and should be retried.
    reset_buffer = 5  # seconds past the reset time before retrying
    slowdown_threshold = 500

    # Gateway errors (e.g. 502) carry no rate limit headers - don't mistake a missing header for an exhausted limit
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_time = response.headers.get("X-RateLimit-Reset")
    retry_after = response.headers.get("Retry-After")
    seconds_until_reset = max(int(reset_time) - time.time(), 0) if reset_time else None

    if retry_after is not None and response.status_code in [403, 429]:
        # Secondary rate limit
        sleep_time = int(retry_after) + reset_buffer
    elif remaining == "0" or response.status_code == 429:
        sleep_time = seconds_until_reset + reset_buffer if seconds_until_reset is not None else 60
    elif response.status_code == 403 and "secondary rate limit" in response.text.lower():
        # Secondary rate limit without Retry-After: GitHub asks to wait at least a minute
        sleep_time = 60
    else:
        # No fixed delay while there is plenty of budget left - only pace requests when it runs low
        if remaining is not None and int(remaining) < slowdown_threshold and seconds_until_reset is not None:
            # Spread the remaining requests over the time left until the reset; the worker threads share
            # one budget, so each thread waits proportionally longer
            delay = seconds_until_reset / max(int(remaining), 1) * MAX_WORKERS
            logger.info(
                f"Rate limit close to being exceeded ({remaining} remaining, resets in {seconds_until_reset:.0f}s). "
                f"Slowing down to 1 request every {delay:.1f} seconds per worker"
            )
            time.sleep(delay)
        return False

    logger.info(f"Remaining: {remaining} | Status Code: {response.status_code}")
    logger.info(f"Rate limit exceeded. Sleeping for {sleep_time:.0f} seconds...")
    time.sleep(sleep_time)
    return True
