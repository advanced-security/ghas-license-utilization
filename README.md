# GHAS activation and coverage optimization

The idea of the project is to optimze the utilization of GHAS licenses within your organization. GHAS has a licensing model that is based on active committers. Each active committer will consume a GHAS licenses. This means that any repositories that this committer is contributing to could have GHAS enabled.

Example:

- Developer A is contributing to 3 repositories - Repo1, Repo2, Repo5
- Developer B is contributing to 2 repositories - Repo2, Repo5
- GHAS is enabled on Repo1, Repo2
- Developer A and B are both active committers to Repo5 as well
- GHAS can be enabled on on Repo5 without consumtions of additional GHAS licenses

## How the script works

The python script takes the inputs:

- Active committers - CSV report about active committers in your enterprise
- GitHub Enterprise slug
- GitHub Organization slug
- GitHub Personal Access Token
- Output file name
- Output file format (Text or JSON)

It will first gather the list of all repositories in the enterprise or organization and their GHAS enabled and craete a list of objects. It will then parse the `Active committers` report and add the active committers to each repository object.

The script will then go through the list and find the repositories that will not require extra GHAS license to enable. It will categorize those into two groups: repositories who's active committers already consume a GHAS license and repositories who do not have active committers.

It will then output the results into a file.

### Active committers

The maximum active committers report is a CSV file that contains the following columns:

```csv
User login,Organization / repository,Last pushed date
theztefan,thez-org/repo_name,2023-09-06
theztefan,thez-org/repo_name3,2023-10-06
theztefan,thez-org/repo_name2,2023-08-06
```

We will be using the StaffTools UI to generate this report from the Enterprise Settings of our GitHub Enterprise Cloud instance.

### GHAS status

We are getting the GHAS status for each repository in an organization by calling `GET /orgs/{org}/repos` API call.

## Output report

The script will output a report that will contain the following information:

```text
GHAS activation and coverage optimization
----------------------------------------
# Current coverage
Total active committers: 1
Total repositories with GHAS: 16
Total repositories without GHAS: 29
Coverage: 35.55555555555556%
----------------------------------------
Turning GHAS on following repositories will not use any new licenses
1. With active comitters already consume GHAS license:
	 -  thez-org/central-config
     ...
2. Without active committers:
	 -  thez-org/go-gin-example
	 -  thez-org/rails-ex
	 -  thez-org/rails-react-typescript-docker-example
     ...
----------------------------------------
# End state coverage
Total repositories with GHAS: 45
Coverage: 100.0%
````

or `JSON` for machine parsable output to plug in GHAS enablement script:
```json
{
    "total_active_committers": 1,
    "total_repos_with_ghas": 16,
    "total_repos_without_ghas": 29,
    "repos_without_ghas_with_active_committers": [
        "thez-org/central-config"
        ...
    ],
    "repos_without_ghas_and_committers": [
        "thez-org/go-gin-example",
        "thez-org/rails-ex",
        "thez-org/rails-react-typescript-docker-example",
        ...
    ]
}
```

## How to run the script

### Prerequisites

- Python 3.9+
- Personal Access Token with permissions depending on the scope you plan yo tun it - `repo`, `admin:org`, `admin:enterprise`
- Active committers report saved locally

### Running

- create a virtual environment - `python3 -m venv venv`
- activate your virtual environment - `source venv/bin/activate`
- install dependencies  `pip3 install -r requirements.txt`
- Set GitHub PAT into `GITHUB_TOKEN` environment variable - `export GITHUB_TOKEN=<token>`
- run the script `python3 main.py --ac-report ghas_maximum_committers_thezenterprise.csv --org thez-org --enterprise thez-enterprise` 