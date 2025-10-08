import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from github import get_ghas_status_for_repos, get_orgs_in_ent, get_active_committers_in_last_90_days


class TestGHESSupport(unittest.TestCase):
    """Test that GHES server URLs are properly handled"""

    def setUp(self):
        self.token = "test_token"
        self.github_com_url = "https://api.github.com"
        self.ghes_url = "https://github.example.com/api/v3"

    @patch("github.requests.get")
    def test_get_ghas_status_uses_custom_server_url(self, mock_get):
        """Test that get_ghas_status_for_repos uses custom server URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.links = {}
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_get.return_value = mock_response

        # Test with GHES URL
        get_ghas_status_for_repos("test-org", self.token, self.ghes_url)
        
        # Verify the URL was constructed correctly
        call_args = mock_get.call_args
        self.assertTrue(call_args[0][0].startswith(self.ghes_url))
        self.assertIn("test-org", call_args[0][0])

    @patch("github.requests.get")
    def test_get_ghas_status_uses_default_github_url(self, mock_get):
        """Test that get_ghas_status_for_repos uses default GitHub.com URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.links = {}
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_get.return_value = mock_response

        # Test with default URL (not passing server_url)
        get_ghas_status_for_repos("test-org", self.token)
        
        # Verify the URL was constructed correctly
        call_args = mock_get.call_args
        self.assertTrue(call_args[0][0].startswith(self.github_com_url))

    @patch("github.requests.post")
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
        call_args = mock_post.call_args
        self.assertIn("graphql", call_args[0][0])
        self.assertTrue(call_args[0][0].startswith(self.ghes_url))

    @patch("github.requests.post")
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
        call_args = mock_post.call_args
        self.assertIn("graphql", call_args[0][0])
        self.assertTrue(call_args[0][0].startswith(self.ghes_url))


if __name__ == "__main__":
    unittest.main()
