class Repository:
    def __init__(self, name, org, ghas_status, pushed_at, active_committers=None):
        self.name = name
        self.org = org
        self.ghas_status = ghas_status
        self.pushed_at = pushed_at
        self.active_committers = (
            active_committers if active_committers is not None else []
        )

    def add_committer(self, committer):
        self.active_committers.append(committer)

    def get_active_committers(self):
        return self.active_committers

    def get_ghas_status(self):
        return self.ghas_status

    def get_pushed_at(self):
        return self.pushed_at

    def get_full_name(self):
        return self.org + "/" + self.name

    def __str__(self):
        return f"Repository: {self.name} | GHAS Status: {self.ghas_status} | Last Pushed At: {self.pushed_at} | Active Committers: {self.active_committers}"

    def to_dict(self):
        return {
            "name": self.name,
            "org": self.org,
            "ghas_status": self.ghas_status,
            "pushed_at": self.pushed_at,
            "active_committers": self.active_committers,
        }


class Report:
    def __init__(
        self,
        all_repos=[],
        active_committers=set(),
        current_active_committers=set(),
        current_repos_with_ghas=[],
        current_repos_without_ghas_with_active_committers=[],
        current_repos_without_ghas_and_committers=[],
        new_active_committers=set(),
        max_coverage_repos=[],
    ):
        self.all_repos = all_repos
        self.active_committers = active_committers
        self.current_active_commiters = current_active_committers
        self.current_repos_with_ghas = current_repos_with_ghas
        self.current_repos_without_ghas_with_active_committers = (
            current_repos_without_ghas_with_active_committers
        )
        self.current_repos_without_ghas_and_committers = (
            current_repos_without_ghas_and_committers
        )
        self.new_active_committers = new_active_committers
        self.max_coverage_repos = max_coverage_repos

    @property
    def total_repos(self):
        return len(self.all_repos)

    @property
    def total_active_committers(self):
        return len(self.active_committers)

    @property
    def total_current_repos_with_ghas(self):
        return len(self.current_repos_with_ghas)

    @property
    def total_current_repos_without_ghas(self):
        return len(self.all_repos) - self.total_current_repos_with_ghas

    @property
    def current_coverage_percentage(self):
        return round((self.total_current_repos_with_ghas / self.total_repos * 100), 2)

    @property
    def new_coverage_percentage(self):
        sum_activated_repos = (
            len(self.current_repos_without_ghas_with_active_committers)
            + len(self.current_repos_without_ghas_and_committers)
            + self.total_current_repos_with_ghas
            + len(self.max_coverage_repos)
        )
        return round((sum_activated_repos / self.total_repos * 100), 2)

    @property
    def new_total_ghas_repos(self):
        return (
            self.total_current_repos_with_ghas
            + len(self.current_repos_without_ghas_and_committers)
            + len(self.current_repos_without_ghas_with_active_committers)
            + len(self.max_coverage_repos)
        )

    def __str__(self):
        return f"""
            Total Active Committers: {self.total_active_committers} \n
            Active Committers: {self.active_committers} \n
            Total Repositories: {self.total_repos} \n
            \tRepos: {', '.join(repo.name for repo in self.all_repos)} \n
            Total Repositories with GHAS: {self.total_current_repos_with_ghas} \n
            \tRepos with GHAS: {', '.join(repo.name for repo in self.current_repos_with_ghas)} \n
            Total Repositories without GHAS: {self.total_current_repos_without_ghas} \n
            Total Repositories without GHAS and Active Committers: {len(self.current_repos_without_ghas_with_active_committers)} \n
            \tRepos without GHAS and Active Committers: {', '.join(f"{repo.name} ({', '.join(repo.get_active_committers())})" for repo in self.current_repos_without_ghas_with_active_committers)} \n'
            Total Repositories without GHAS and Committers: {len(self.current_repos_without_ghas_and_committers)} \n
            \tRepos without GHAS and Committers: {', '.join(repo.name for repo in self.current_repos_without_ghas_and_committers)} \n
            Total New Active Committers: {len(self.new_active_committers)} \n
            \tNew Active Committers: {', '.join(self.new_active_committers)} \n
            Repositories to Max Coverage: {len(self.max_coverage_repos)} \n
             {', '.join(f'{repo.name} (Active committers: {", ".join(repo.active_committers)})' for repo in self.max_coverage_repos)} \n
        """

    def to_dict(self):
        return {
            "all_repos": [repo.to_dict() for repo in self.all_repos],
            "active_committers": list(self.active_committers),
            "current_active_commiters": list(self.current_active_commiters),
            "current_repos_with_ghas": [
                repo.to_dict() for repo in self.current_repos_with_ghas
            ],
            "current_repos_without_ghas_with_active_committers": [
                repo.to_dict()
                for repo in self.current_repos_without_ghas_with_active_committers
            ],
            "current_repos_without_ghas_and_committers": [
                repo.to_dict()
                for repo in self.current_repos_without_ghas_and_committers
            ],
            "new_active_committers": list(self.new_active_committers),
            "max_coverage_repos": [repo.to_dict() for repo in self.max_coverage_repos],
        }
