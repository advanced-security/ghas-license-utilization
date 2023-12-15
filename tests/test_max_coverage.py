import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import random
from datetime import datetime
from custom_test_runner import CustomTextTestRunner
from colorama import Fore, Style
from models import Repository
from report import (
    find_combination_with_max_repositories_greedy,
    find_combination_with_max_repositories,
)


class TestMaxRepositoriesCoverageAlgorithm(unittest.TestCase):
    def test_find_combination_with_max_repositories_brueforce(self):
        no_repos = 20
        no_users = 20
        license_count = 5

        repositories = [
            Repository(
                name=f"repo{i}",
                org="org",
                ghas_status=random.choice(["enabled", "disabled"]),
                visibility="private",
                pushed_at=datetime.now().isoformat(),
                active_committers=[
                    f"user{j}" for j in range(random.randint(1, no_users))
                ],
            )
            for i in range(no_repos)
        ]

        combination, unique_committers = find_combination_with_max_repositories(
            repositories, license_count, set()
        )

        # Check that the number of unique active committers does not exceed the license limit
        self.assertLessEqual(len(unique_committers), license_count)

        print(f"Number of unique active committers: {len(unique_committers)}")
        print(f"Number of repositories in the combination: {len(combination)}")
        print(f"The unique active committers are: {unique_committers}")
        # print(f"The combination: {[str(repo) for repo in combination]}")

        # Check that all repositories in the combination are in the original list
        for repo in combination:
            self.assertIn(repo, repositories)

    def test_find_combination_with_max_repositories_greedy(self):
        no_repos = 2000
        no_users = 20
        license_count = 5

        repositories = [
            Repository(
                name=f"repo{i}",
                org="org",
                ghas_status=random.choice(["enabled", "disabled"]),
                visibility="private",
                pushed_at=datetime.now().isoformat(),
                active_committers=[
                    f"user{j}" for j in range(random.randint(1, no_users))
                ],
            )
            for i in range(no_repos)
        ]

        combination, unique_committers = find_combination_with_max_repositories_greedy(
            repositories, license_count, set()
        )

        # Check that the number of unique active committers does not exceed the license limit
        self.assertLessEqual(len(unique_committers), license_count)

        print(f"Number of unique active committers: {len(unique_committers)}")
        print(f"Number of repositories in the combination: {len(combination)}")
        print(f"The unique active committers are: {unique_committers}")

        # Check that all repositories in the combination are in the original list
        for repo in combination:
            self.assertIn(repo, repositories)

    def test_find_combination_with_max_repositories_bruteforce_vs_greedy(self):
        no_repos = 20
        no_users = 20
        no_license = 5
        # Create a mock list of 200 repositories
        repositories = [
            Repository(
                name=f"repo{i}",
                org="org",
                ghas_status=random.choice(["enabled", "disabled"]),
                visibility="private",
                pushed_at=datetime.now().isoformat(),
                active_committers=[
                    f"user{j}" for j in range(random.randint(1, no_users))
                ],
            )
            for i in range(no_repos)
        ]
        result1, _ = find_combination_with_max_repositories(
            repositories, no_license, set()
        )
        result2, _ = find_combination_with_max_repositories_greedy(
            repositories, no_license, set()
        )
        self.assertEqual(
            set(repo.name for repo in result1), set(repo.name for repo in result2)
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestMaxRepositoriesCoverageAlgorithm
    )
    CustomTextTestRunner().run(suite)
