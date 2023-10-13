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
