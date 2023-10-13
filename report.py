import csv
import json


def add_active_committers(report, repositories):
    with open(report, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            user_login, org_repo, _ = row
            org, repo_name = org_repo.split("/")
            for repo in repositories:
                if repo.name == repo_name and repo.org == org:
                    repo.add_committer(user_login)


def generate_ghas_coverage_report(repositories):
    active_committers = set()
    repos_with_ghas = []
    committers_in_ghas_repos = set()
    repos_without_ghas_with_active_committers = []
    repos_without_ghas_and_committers = []

    for repo in repositories:
        repo_active_committers = repo.get_active_committers()
        active_committers.update(repo_active_committers)

        if repo.get_ghas_status():
            repos_with_ghas.append(repo)
            committers_in_ghas_repos.update(repo_active_committers)
        else:
            if any(
                committer in committers_in_ghas_repos
                for committer in repo_active_committers
            ):
                repos_without_ghas_with_active_committers.append(repo)
            elif not repo_active_committers:
                repos_without_ghas_and_committers.append(repo)

    total_active_committers = len(active_committers)
    total_repos_with_ghas = len(repos_with_ghas)
    total_repos_without_ghas = len(repositories) - total_repos_with_ghas

    return {
        "total_active_committers": total_active_committers,
        "total_repos_with_ghas": total_repos_with_ghas,
        "total_repos_without_ghas": total_repos_without_ghas,
        "repos_without_ghas_with_active_committers": [
            repo.get_full_name() for repo in repos_without_ghas_with_active_committers
        ],
        "repos_without_ghas_and_committers": [
            repo.get_full_name() for repo in repos_without_ghas_and_committers
        ],
    }


def write_report(results, output, output_format):
    if output_format == "json":
        with open(output, "w") as file:
            json.dump(results, file)
    else:
        with open(output, "w") as file:
            print(f"GHAS activation and coverage optimization", file=file)
            print(f"--" * 20, file=file)
            print(f"# Current coverage", file=file)
            print(
                f"Total active committers: {results['total_active_committers']}",
                file=file,
            )
            print(
                f"Total repositories with GHAS: {results['total_repos_with_ghas']}",
                file=file,
            )
            print(
                f"Total repositories without GHAS: {results['total_repos_without_ghas']}",
                file=file,
            )

            coverage_percentage = round(
                (
                    results["total_repos_with_ghas"]
                    / (
                        results["total_repos_with_ghas"]
                        + results["total_repos_without_ghas"]
                    )
                    * 100
                ),
                2,
            )
            print(f"Coverage: {coverage_percentage}%", file=file)
            print(f"--" * 20, file=file)
            print(
                f"Turning GHAS on following repositories will not use any new licenses",
                file=file,
            )
            print(f"1. With active comitters already consume GHAS license:", file=file)
            for repo in results["repos_without_ghas_with_active_committers"]:
                print(f"\t - ", repo, file=file)

            print(f"2. Without active committers:", file=file)
            for repo in results["repos_without_ghas_and_committers"]:
                print(f"\t - ", repo, file=file)

            sum_activated_repos = (
                len(results["repos_without_ghas_with_active_committers"])
                + len(results["repos_without_ghas_and_committers"])
                + results["total_repos_with_ghas"]
            )
            coverage_percentage = round(
                (
                    sum_activated_repos
                    / (
                        results["total_repos_with_ghas"]
                        + results["total_repos_without_ghas"]
                    )
                    * 100
                ),
                2,
            )
            print(f"--" * 20, file=file)
            print(f"# End state coverage", file=file)
            print(
                f"Total repositories with GHAS: {sum_activated_repos}",
                file=file,
            )
            print(f"Coverage: {coverage_percentage}%", file=file)
