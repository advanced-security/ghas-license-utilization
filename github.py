import requests
import csv
import time
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from models import Repository
from helpers import *

logger = get_logger()


RATE_LIMIT_LOCK = threading.Lock()
MAX_WORKERS = 5


def add_active_committers(report, repositories, token):
    try:
        with open(report, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                user_login, org_repo, *_ = row
                org, repo_name = org_repo.split("/")
                for repo in repositories:
                    if repo.name == repo_name and repo.org == org:
                        repo.add_committer(user_login)
    except (Exception, TypeError) as e:
        logger.info(f"Fetching active committers from GitHub API...")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(
                    get_active_committers_in_last_90_days, repo.org, repo.name, token
                )
                for repo in repositories
            ]
            for i, future in enumerate(
                concurrent.futures.as_completed(futures), start=1
            ):
                repo = repositories[i - 1]
                logger.info(
                    f"[{i}/{len(repositories)}] Processing repository: {repo.get_full_name()}"
                )
                repo.add_active_committers(future.result())


def get_organizations(args, token):
    orgs_in_ent = []
    if not args.enterprise:
        orgs_in_ent.append(args.organization)
    else:
        orgs_in_ent = get_orgs_in_ent(args.enterprise, token)
    return orgs_in_ent


def process_organizations(orgs_in_ent, token):
    total_repositories = []
    for i, org in enumerate(orgs_in_ent, start=1):
        logger.info(f"[{i}/{len(orgs_in_ent)}] Processing organization: {org}")
        total_repositories.extend(get_ghas_status_for_repos(org, token))
    return total_repositories


def get_ghas_status_for_repos(org, token):
    url = f"https://api.github.com/orgs/{org}/repos?per_page=100"
    headers = {"Authorization": f"token {token}"}
    page = 1
    repos = []

    while True:
        response = requests.get(url, headers=headers, params={"page": page})

        handle_rate_limit(response)

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
            repo = Repository(name, owner, ghas_status, visibility, pushed_at)
            repos.append(repo)
        if "next" not in response.links:
            break
        page += 1

    return repos


def get_active_committers_in_last_90_days(org, repo, token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"token {token}"}
    active_committers = set()

    end_cursor = None
    while True:
        query = """
        query getCommitters($org: String!, $repo: String!, $since: GitTimestamp!, $after: String) {
            repository(owner: $org, name: $repo) {
                visibility
                refs(refPrefix: "refs/heads/", first: 100) {
                    nodes {
                        name
                        target {
                            ... on Commit {
                                history(first: 100, since: $since, after: $after) {
                                    nodes {
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
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        hasNextPage = False
        since = (datetime.now() - timedelta(days=90)).isoformat()
        variables = {"org": org, "repo": repo, "since": since, "after": end_cursor}
        payload = {"query": query, "variables": variables}
        response = requests.post(url, headers=headers, json=payload)

        handle_rate_limit(response)

        if response.status_code != 200:
            logger.info(f"Response: {response.json()}")
            next

        if response.status_code == 401:
            logger.info(f"Insufficient permissions token provided.")
            break

        data = response.json()
        repository = data["data"]["repository"]
        refs = repository.get("refs")
        visibility = repository.get("visibility")

        # only process if repository is not public
        if visibility != "PUBLIC":
            if refs:
                nodes = refs.get("nodes", [])
                for ref in nodes:
                    target = ref.get("target", {})
                    history = target.get("history") if target else None
                    if history:
                        commits = history.get("nodes", [])
                        for commit in commits:
                            user = commit["author"]["user"]
                            if user:
                                author = user["login"]
                                active_committers.add(author)
                        end_cursor = history.get("pageInfo", {}).get("endCursor")
                        hasNextPage = history.get("pageInfo", {}).get("hasNextPage")

        if not refs or not hasNextPage:
            break

        handle_rate_limit(response)

    # Remove dependabot[bot] from active committers
    active_committers.discard("dependabot[bot]")

    return list(active_committers)


def get_orgs_in_ent(enterprise_name, token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"token {token}", "X-Github-Next-Global-ID": "true"}
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
        payload = {"query": query, "variables": variables}
        response = requests.post(url, headers=headers, json=payload)

        handle_rate_limit(response)

        data = response.json()
        orgs += [
            org["login"] for org in data["data"]["enterprise"]["organizations"]["nodes"]
        ]
        if data["data"]["enterprise"]["organizations"]["pageInfo"]["hasNextPage"]:
            end_cursor = data["data"]["enterprise"]["organizations"]["pageInfo"][
                "endCursor"
            ]
        else:
            break

        handle_rate_limit(response)
    return orgs


def handle_rate_limit(response):
    # Check the rate limit
    remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 50:
        logger.info(f"Rate limit close to being exceeded. Slowing down requests...")
        time.sleep(5)
    if remaining == 0 or response.status_code in [403, 429]:
        with RATE_LIMIT_LOCK:
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            if remaining == 0 or response.status_code in [403, 429]:
                logger.info(f"Headers: {response.headers}")
                if "Retry-After" in response.headers:
                    sleep_time = int(response.headers["Retry-After"]) + 2
                else:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    sleep_time = max(
                        reset_time - time.time() + 2, 1
                    )  # Ensure sleep time is at least 1 second
                logger.info(
                    f"Rate limit exceeded. Sleeping for {sleep_time} seconds..."
                )
                time.sleep(sleep_time)
    time.sleep(1)  # Sleep for 1 second anyways to avoid hitting rate limit
