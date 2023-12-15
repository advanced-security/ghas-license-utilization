import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from custom_test_runner import CustomTextTestRunner
from datetime import datetime
from github import get_active_committers_in_last_90_days, get_ghas_status_for_repos
from github import add_active_committers
from models import Repository
from main import process_organizations
from helpers import get_logger

logger = get_logger()


class TestActiveCommitters(unittest.TestCase):
    def setUp(self):
        self.org = "thez-org"
        self.repo = "hilly"
        self.token = os.getenv("GITHUB_TOKEN")
        self.report = "test-report.csv"
        self.repositories = [
            Repository(self.repo, self.org, False, datetime.now().isoformat(), None)
        ]

    def test_active_committers_one_repo(self):
        # Get active committers using get_active_committers_in_last_90_days()
        active_committers_1 = get_active_committers_in_last_90_days(
            self.org, self.repo, self.token
        )

        # Get active committers using add_active_committers()
        add_active_committers(self.report, self.repositories, self.token)
        active_committers_2 = self.repositories[0].get_active_committers()

        # Compare the results
        self.assertCountEqual(active_committers_1, active_committers_2)

    def test_active_committers_one_org_all_repos(self):
        # Get all repositories for the organization
        all_repos = process_organizations([self.org], self.token)
        add_active_committers(self.report, all_repos, self.token)

        for repo in all_repos:
            # Get active committers using get_active_committers_in_last_90_days()
            active_committers_1 = get_active_committers_in_last_90_days(
                self.org, repo.name, self.token
            )

            active_committers_2 = repo.get_active_committers()
            # Compare the results
            logger.info(
                f"Comparing active committers for {repo.name} - {repo.org} - {len(active_committers_1)} - {len(active_committers_2)} - GraphQL API: {active_committers_1} - CSV: {active_committers_2}"
            )
            self.assertCountEqual(active_committers_1, active_committers_2)


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestActiveCommitters)
    CustomTextTestRunner().run(suite)