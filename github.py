import requests
import csv
import time
import threading
import concurrent.futures
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from models import Repository
from helpers import *

logger = get_logger()


RATE_LIMIT_LOCK = threading.Lock()
MAX_WORKERS = 5


def add_active_committers(report, repositories, token, server_url="https://api.github.com"):
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
                    get_active_committers_in_last_90_days, repo.org, repo.name, token, server_url
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
        orgs_in_ent = get_orgs_in_ent(args.enterprise, token, args.server_url)
    return orgs_in_ent


def process_organizations(orgs_in_ent, token, server_url="https://api.github.com"):
    total_repositories = []
    for i, org in enumerate(orgs_in_ent, start=1):
        logger.info(f"[{i}/{len(orgs_in_ent)}] Processing organization: {org}")
        total_repositories.extend(get_ghas_status_for_repos(org, token, server_url))
    return total_repositories


def get_ghas_status_for_repos(org, token, server_url="https://api.github.com"):
    url = f"{server_url}/orgs/{org}/repos?per_page=100"
    headers = {"Authorization": f"token {token}"}
    page = 1
    repos = []

    while True:
        response = requests.get(url, headers=headers, params={"page": page})

        handle_rate_limit(response)

        # Check for HTTP errors
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code} error for URL {url}")
            logger.error(f"Response: {response.text}")
            if response.status_code == 401:
                raise Exception(f"Authentication failed for organization {org}. Please check your GitHub token is valid for the server {server_url}")
            elif response.status_code == 404:
                raise Exception(f"Organization '{org}' not found or not accessible. Please check the organization name and your token permissions.")
            else:
                raise Exception(f"Failed to fetch repositories for organization {org}. Status: {response.status_code}")

        data = response.json()
        
        # Check if data is a list (successful response) or dict (error response)
        if not isinstance(data, list):
            logger.error(f"Unexpected response format: {data}")
            raise Exception(f"API returned an error: {data.get('message', 'Unknown error')}")
            
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


def get_active_committers_in_last_90_days(org, repo, token, server_url="https://api.github.com"):
    # For GHES, the GraphQL endpoint is at /api/graphql, for GitHub.com it's at /graphql
    if server_url != "https://api.github.com":
        # For GHES: Remove any /api/vX suffix to get base URL (supports v3, v4, v44, etc.)
        base_url = re.sub(r'/api/v\d+$', '', server_url)
        graphql_url = f"{base_url}/api/graphql"
    else:
        graphql_url = f"{server_url}/graphql"
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
        response = requests.post(graphql_url, headers=headers, json=payload)

        handle_rate_limit(response)

        if response.status_code != 200:
            logger.info(f"Response: {response.json()}")
            continue

        if response.status_code == 401:
            logger.info(f"Insufficient permissions token provided.")
            break

        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            logger.error(f"GraphQL errors for {org}/{repo}: {data['errors']}")
            break
            
        # Check if data structure is valid
        if "data" not in data or not data["data"] or "repository" not in data["data"]:
            logger.error(f"Invalid GraphQL response structure for {org}/{repo}: {data}")
            break
            
        repository = data["data"]["repository"]
        
        # Handle case where repository is None (e.g., doesn't exist or no access)
        if repository is None:
            logger.warning(f"Repository {org}/{repo} not found or not accessible")
            break
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


def get_orgs_in_ent(enterprise_name, token, server_url="https://api.github.com"):
    # For GHES, the GraphQL endpoint is at /api/graphql, for GitHub.com it's at /graphql
    if server_url != "https://api.github.com":
        # For GHES: Remove any /api/vX suffix to get base URL (supports v3, v4, v44, etc.)
        base_url = re.sub(r'/api/v\d+$', '', server_url)
        graphql_url = f"{base_url}/api/graphql"
    else:
        graphql_url = f"{server_url}/graphql"
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
        response = requests.post(graphql_url, headers=headers, json=payload)

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
