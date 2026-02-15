import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from custom_test_runner import CustomTextTestRunner
from models import Repository
from github import get_ghas_status_for_repos


class TestArchivedRepositoryFiltering(unittest.TestCase):

    @patch("github.requests.get")
    def test_get_ghas_status_filters_archived_repos(self, mock_get):
        """Test that get_ghas_status_for_repos filters out archived repositories"""
        # Mock API response with mix of archived and non-archived repos
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "full_name": "test-org/active-repo",
                "archived": False,
                "visibility": "private",
                "pushed_at": "2023-11-22T11:39:41Z",
                "security_and_analysis": {"advanced_security": {"status": "enabled"}},
            },
            {
                "full_name": "test-org/archived-repo",
                "archived": True,
                "visibility": "private",
                "pushed_at": "2023-01-15T10:20:30Z",
                "security_and_analysis": {"advanced_security": {"status": "disabled"}},
            },
            {
                "full_name": "test-org/another-active-repo",
                "archived": False,
                "visibility": "public",
                "pushed_at": "2023-12-01T14:25:15Z",
                "security_and_analysis": {"advanced_security": {"status": "disabled"}},
            },
        ]
        mock_response.links = {}  # No pagination
        mock_response.headers = {
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Reset": "1234567890",
        }
        mock_get.return_value = mock_response

        # Call the function
        repos = get_ghas_status_for_repos("test-org", "fake-token")

        # Verify only non-archived repos are returned
        self.assertEqual(len(repos), 2)
        repo_names = [repo.name for repo in repos]
        self.assertIn("active-repo", repo_names)
        self.assertIn("another-active-repo", repo_names)
        self.assertNotIn("archived-repo", repo_names)

        # Verify all returned repos are non-archived (they wouldn't be returned otherwise)
        for repo in repos:
            self.assertIsNotNone(repo.name)

    @patch("github.requests.get")
    def test_get_ghas_status_handles_missing_archived_field(self, mock_get):
        """Test that get_ghas_status_for_repos handles missing archived field gracefully"""
        # Mock API response without archived field (should default to False)
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "full_name": "test-org/repo-without-archived-field",
                # Note: no "archived" field
                "visibility": "private",
                "pushed_at": "2023-11-22T11:39:41Z",
                "security_and_analysis": {"advanced_security": {"status": "enabled"}},
            }
        ]
        mock_response.links = {}  # No pagination
        mock_response.headers = {
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Reset": "1234567890",
        }
        mock_get.return_value = mock_response

        # Call the function
        repos = get_ghas_status_for_repos("test-org", "fake-token")

        # Verify repo is included (archived defaults to False when missing)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].name, "repo-without-archived-field")

    @patch("github.requests.get")
    def test_get_ghas_status_filters_all_archived_repos(self, mock_get):
        """Test that get_ghas_status_for_repos returns empty list when all repos are archived"""
        # Mock API response with only archived repos
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "full_name": "test-org/archived-repo-1",
                "archived": True,
                "visibility": "private",
                "pushed_at": "2023-01-15T10:20:30Z",
                "security_and_analysis": {"advanced_security": {"status": "disabled"}},
            },
            {
                "full_name": "test-org/archived-repo-2",
                "archived": True,
                "visibility": "public",
                "pushed_at": "2023-02-20T15:30:45Z",
                "security_and_analysis": {"advanced_security": {"status": "enabled"}},
            },
        ]
        mock_response.links = {}  # No pagination
        mock_response.headers = {
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Reset": "1234567890",
        }
        mock_get.return_value = mock_response

        # Call the function
        repos = get_ghas_status_for_repos("test-org", "fake-token")

        # Verify no repos are returned
        self.assertEqual(len(repos), 0)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestArchivedRepositoryFiltering
    )
    CustomTextTestRunner().run(suite)
