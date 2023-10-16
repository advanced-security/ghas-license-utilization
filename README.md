# GHAS Activation and Coverage Optimization

The idea of the project is to optimize the utilization of GHAS licenses within your organization. GHAS has a licensing model that is based on active committers. Each active committer will consume a GHAS license. This means that any repositories to which this committer is contributing could have GHAS enabled.

Example:

- Developer A is contributing to 3 repositories - `Repo1`, `Repo2`, `Repo5`.
- Developer B is contributing to 2 repositories - `Repo2`, `Repo5`.
- GHAS is enabled on `Repo1` and `Repo2`.
- Developer A and B are both active committers for `Repo5` as well.
- GHAS can be enabled on `Repo5` without consuming additional GHAS licenses.

## How the Script Works

The Python script takes the following inputs:

- Active committers: CSV report about active committers in your enterprise.
- GitHub Enterprise slug.
- GitHub Organization slug.
- GitHub Personal Access Token.
- Output file name.
- Output file format (Text or JSON).

It will first gather the list of all repositories in the enterprise or organization and their GHAS enabled status and create a list of objects. It will then parse the `Active committers` report and add the active committers to each repository object.

The script will then go through the list and find the repositories that will not require extra GHAS licenses to enable. It will categorize those into two groups: repositories whose active committers already consume a GHAS license and repositories that do not have active committers.

It will then output the results into a file.

### Active Committers

The maximum active committers report is a CSV file that contains the following columns:

```csv
User login,Organization / repository,Last pushed date
theztefan,thez-org/repo_name,2023-09-06
theztefan,thez-org/repo_name3,2023-10-06
theztefan,thez-org/repo_name2,2023-08-06
```

We will be using the Stafftools UI to generate this report.

### GHAS status

We obtain the GHAS status for each repository in an organization by calling the `GET /orgs/{org}/repos` API endpoint.

## Output report

The script will output a report that will contain the following information:

```text
GHAS activation and coverage optimization
----------------------------------------
# Current coverage
Total active committers: 1
Total repositories with GHAS: 16
Total repositories without GHAS: 29
Coverage: 35.56%
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

or `JSON`  for machine-parseable output to plug in GHAS enablement script:

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

### Usage

```text
usage: main.py [-h] --ac-report AC_REPORT [--enterprise ENTERPRISE] [--organization ORGANIZATION] [--output OUTPUT] [--output-format OUTPUT_FORMAT] [--token TOKEN]

GHAS activation and coverage activation

options:
  -h, --help            show this help message and exit
  --ac-report AC_REPORT
                        Path to the active committers report
  --enterprise ENTERPRISE
                        Name of the enterprise
  --organization ORGANIZATION
                        Name of the organization
  --output OUTPUT       Path to the output file
  --output-format OUTPUT_FORMAT
                        Output format - text or json
  --token TOKEN         GitHub Personal Access Token (if not set in GITHUB_TOKEN envrionment variable)
```

### Prerequisites

- Python 3.9+
- Personal Access Token (PAT) with permissions depending on the scope you plan to run it - `repo`, `admin:org`, `admin:enterprise`
- Active committers report saved locally

### Running

- Create a virtual environment - `python3 -m venv venv`
- Activate your virtual environment - `source venv/bin/activate`
- Install dependencies  `pip3 install -r requirements.txt`
- Set GitHub PAT into `GITHUB_TOKEN` environment variable - `export GITHUB_TOKEN=<token>`
- Run the script `python3 main.py --ac-report ghas_maximum_committers_thezenterprise.csv --org thez-org --enterprise thez-enterprise`
