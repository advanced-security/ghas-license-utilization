import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from github import (
    GitHubAPIError,
    add_active_committers_from_api,
    get_active_committers_in_last_90_days,
    get_ghas_status_for_repos,
    get_graphql_url,
    get_orgs_in_ent,
)
from models import Repository


class TestGHESSupport(unittest.TestCase):
    """Test that GHES server URLs are properly handled"""

    def setUp(self):
        self.token = "test_token"
        self.github_com_url = "https://api.github.com"
        self.ghes_url = "https://github.example.com/api/v3"
        self.ghes_graphql_url = "https://github.example.com/api/graphql"

    @patch("github.requests.Session.request")
    def test_get_ghas_status_uses_custom_server_url(self, mock_get):
        """Test that get_ghas_status_for_repos uses custom server URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.links = {}
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_get.return_value = mock_response

        # Test with GHES URL
        get_ghas_status_for_repos("test-org", self.token, self.ghes_url)
        
        # Verify the URL was constructed correctly
        method, url = mock_get.call_args[0]
        self.assertEqual(method, "GET")
        self.assertTrue(url.startswith(self.ghes_url))
        self.assertIn("test-org", url)

    @patch("github.requests.Session.request")
    def test_get_ghas_status_uses_default_github_url(self, mock_get):
        """Test that get_ghas_status_for_repos uses default GitHub.com URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.links = {}
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_get.return_value = mock_response

        # Test with default URL (not passing server_url)
        get_ghas_status_for_repos("test-org", self.token)
        
        # Verify the URL was constructed correctly
        method, url = mock_get.call_args[0]
        self.assertTrue(url.startswith(self.github_com_url))

    @patch("github.requests.Session.request")
    def test_get_orgs_in_ent_uses_custom_server_url(self, mock_post):
        """Test that get_orgs_in_ent uses custom GraphQL endpoint for GHES"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "enterprise": {
                    "organizations": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False, "endCursor": None}
                    }
                }
            }
        }
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Test with GHES URL
        get_orgs_in_ent("test-enterprise", self.token, self.ghes_url)
        
        # Verify the GraphQL endpoint was constructed correctly
        method, url = mock_post.call_args[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, self.ghes_graphql_url)

    @patch("github.requests.Session.request")
    def test_get_active_committers_uses_custom_server_url(self, mock_post):
        """Test that get_active_committers_in_last_90_days uses custom GraphQL endpoint"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "visibility": "PRIVATE",
                    "refs": None
                }
            }
        }
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Test with GHES URL
        get_active_committers_in_last_90_days("test-org", "test-repo", self.token, self.ghes_url)
        
        # Verify the GraphQL endpoint was constructed correctly
        method, url = mock_post.call_args[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, self.ghes_graphql_url)

    def test_graphql_url(self):
        """Test GraphQL endpoint mapping for GitHub.com and GHES"""
        self.assertEqual(get_graphql_url(), "https://api.github.com/graphql")
        self.assertEqual(get_graphql_url(self.github_com_url), "https://api.github.com/graphql")
        self.assertEqual(get_graphql_url(self.ghes_url), self.ghes_graphql_url)
        self.assertEqual(get_graphql_url(self.ghes_url + "/"), self.ghes_graphql_url)

    @patch("github.requests.Session.request")
    def test_get_ghas_status_stops_on_401(self, mock_get):
        """Test that an invalid token stops the run instead of returning incomplete results"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.ok = False
        mock_response.headers = {}
        mock_get.return_value = mock_response

        with self.assertRaises(GitHubAPIError) as ctx:
            get_ghas_status_for_repos("test-org", self.token, self.ghes_url)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn(self.ghes_url, str(ctx.exception))

    @patch("github.get_active_committers_in_last_90_days")
    def test_add_active_committers_stops_on_401(self, mock_fetch):
        """Test that a 401 while fetching committers stops the run instead of flagging every repository"""
        mock_fetch.side_effect = GitHubAPIError("401 Unauthorized", 401)
        repos = [Repository(f"repo-{i}", "test-org", False, "private", None) for i in range(10)]

        with self.assertRaises(GitHubAPIError):
            add_active_committers_from_api(repos, self.token, max_workers=1, server_url=self.ghes_url)
        # Queued fetches are cancelled once the 401 is seen
        self.assertLess(mock_fetch.call_count, len(repos))

    @patch("github.get_active_committers_in_last_90_days")
    def test_add_active_committers_continues_on_other_errors(self, mock_fetch):
        """Test that non-auth errors are still flagged per repository without stopping the run"""
        mock_fetch.side_effect = GitHubAPIError("HTTP 502", 502)
        repos = [Repository(f"repo-{i}", "test-org", False, "private", None) for i in range(3)]

        add_active_committers_from_api(repos, self.token, max_workers=1, server_url=self.ghes_url)
        self.assertTrue(all(repo.committers_fetch_failed for repo in repos))


if __name__ == "__main__":
    unittest.main()
