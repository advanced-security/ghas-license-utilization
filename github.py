import requests
from models import Repository


def get_ghas_status_for_repos(org, token):
    url = f"https://api.github.com/orgs/{org}/repos?per_page=100"
    headers = {"Authorization": f"token {token}"}
    page = 1
    repos = []

    while True:
        response = requests.get(url, headers=headers, params={"page": page})
        data = response.json()
        for repo_data in data:
            owner, name = repo_data["full_name"].split("/")
            ghas_status = (
                repo_data.get("security_and_analysis", {})
                .get("advanced_security", {})
                .get("status", "")
                == "enabled"
            )
            pushed_at = repo_data["pushed_at"]
            repo = Repository(name, owner, ghas_status, pushed_at)
            repos.append(repo)
        if "next" not in response.links:
            break
        page += 1
    return repos


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
    return orgs
