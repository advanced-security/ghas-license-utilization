import json
from itertools import combinations
from models import Report


def generate_ghas_coverage_report(repositories):
    result = Report()
    result.all_repos = repositories
    committers_in_ghas_repos = set()
    left_over_repos = []

    for repo in repositories:
        repo_active_committers = repo.get_active_committers()
        result.active_committers.update(repo_active_committers)
        if repo.get_ghas_status():
            result.current_repos_with_ghas.append(repo)
            committers_in_ghas_repos.update(repo_active_committers)
        else:
            left_over_repos.append(repo)

    for repo in left_over_repos:
        active_committers = repo.get_active_committers()
        if active_committers and all(
            committer in committers_in_ghas_repos for committer in active_committers
        ):
            result.current_repos_without_ghas_with_active_committers.append(repo)
        elif not active_committers and repo.get_visibility() != "public":
            result.current_repos_without_ghas_and_committers.append(repo)
        elif repo.get_visibility() == "public":
            result.current_repos_without_ghas_and_public.append(repo)

    result.current_active_commiters = committers_in_ghas_repos
    left_over_repos = []

    for repo in repositories:
        if (
            repo not in result.current_repos_without_ghas_with_active_committers
            and repo not in result.current_repos_without_ghas_and_committers
            and repo not in result.current_repos_with_ghas
            and repo not in result.current_repos_without_ghas_and_public
        ):
            left_over_repos.append(repo)

    return result, left_over_repos


def find_combination_with_max_repositories(
    left_over_repos, license_count, current_active_comitters
):
    max_repositories = 0
    max_new_committers = 0
    max_combination = None

    for r in range(1, len(left_over_repos) + 1):
        repo_combinations = combinations(left_over_repos, r)

        for combination in repo_combinations:
            # Calculate the total number of unique active committers in the combination
            # without including the current active committers
            unique_committers = set()
            for repo in combination:
                unique_committers.update(repo.get_active_committers())
                unique_committers.difference_update(current_active_comitters)

            if len(unique_committers) <= license_count:
                num_repositories = len(combination)
                if num_repositories > max_repositories:
                    max_repositories = num_repositories
                    max_new_committers = unique_committers
                    max_combination = combination

    return max_combination, max_new_committers


def find_combination_with_max_repositories_greedy(
    left_over_repos, license_count, current_active_comitters
):
    # Sort the repositories in descending order by the number of unique active committers
    sorted_repos = sorted(
        left_over_repos,
        key=lambda repo: len(
            set(repo.get_active_committers()).difference(current_active_comitters)
        ),
        reverse=True,
    )

    combination = []
    unique_committers = set()

    # Add repositories to the combination until reaching the license limit
    for repo in sorted_repos:
        new_committers = set(repo.get_active_committers()).difference(
            current_active_comitters
        )
        if len(unique_committers.union(new_committers)) <= license_count:
            combination.append(repo)
            unique_committers.update(new_committers)

    return combination, unique_committers


def generate_max_coverage_report(repositories, license_count=None):
    result, left_over_repos = generate_ghas_coverage_report(repositories)
    if not license_count:
        return result

    result.max_coverage_repos = []

    max_combination, max_committers = find_combination_with_max_repositories_greedy(
        left_over_repos, license_count, result.current_active_commiters
    )

    if max_combination is not None:
        result.max_coverage_repos = max_combination
        result.new_active_committers = max_committers
    else:
        print("No valid combination found.")

    return result


def write_report(report: Report, output_file, output_format):
    if output_format == "json":
        with open(output_file, "w") as file:
            json.dump(report.to_dict(), file)
    else:
        with open(output_file, "w") as file:
            print(f"# GHAS activation and coverage optimization\n", file=file)
            print(f"---" * 20, file=file)
            print(f"# Current coverage\n", file=file)
            print(
                f"Total active committers: {report.total_active_committers}",
                file=file,
            )
            print(
                f"Total repositories with GHAS: {report.total_current_repos_with_ghas}",
                file=file,
            )
            print(
                f"Total repositories without GHAS: {report.total_current_repos_without_ghas}",
                file=file,
            )

            print(f"Coverage: {report.current_coverage_percentage}%", file=file)
            print(f"--" * 20, file=file)
            print(f"# Increase coverage with currently consumed licenses\n", file=file)
            print(
                f"**Turning GHAS on following repositories will not consume additional licenses**",
                file=file,
            )
            print(
                f"- Repositories with active committers already consume GHAS license:",
                file=file,
            )
            for repo in report.current_repos_without_ghas_with_active_committers:
                print(f"\t - ", repo, file=file)

            print(
                f"- Public repositories (do not required GHAS license):",
                file=file,
            )
            for repo in report.current_repos_without_ghas_and_public:
                print(f"\t - ", repo, file=file)

            print(
                f"- Private and Internal repositories without active committers:",
                file=file,
            )
            for repo in report.current_repos_without_ghas_and_committers:
                print(f"\t - ", repo, file=file)
            print(f"--" * 20, file=file)
            if len(report.new_active_committers):
                print(f"# Maximize coverage with additional licenses \n", file=file)
                print(
                    f"**Turning GHAS on following repositories will consume {len(report.new_active_committers)} additional licenses**",
                    file=file,
                )
                print(f"- Combination of repositories to activate GHAS on:", file=file)
                for repo in report.max_coverage_repos:
                    print(f"\t - ", repo, file=file)
                print(
                    f"\n New active comitters that will consume GHAS license:",
                    file=file,
                )
                for committer in report.new_active_committers:
                    print(f"\t - ", committer, file=file)
                print(f"--" * 20, file=file)

            print(f"# End state coverage \n", file=file)
            print(
                f"Total repositories with GHAS: {report.new_total_ghas_repos}",
                file=file,
            )
            print(f"Coverage: {report.new_coverage_percentage}%", file=file)
