# GHAS Activation and Coverage Optimization

The idea of the project is to optimize the utilization of GHAS licenses within your organization. GHAS has a licensing model that is based on active committers. Each active committer will consume a GHAS license. This means that any repositories to which this committer is contributing could have GHAS enabled.

**Example:**

- Developer A is contributing to 3 repositories - `Repo1`, `Repo2`, `Repo5`.
- Developer B is contributing to 2 repositories - `Repo2`, `Repo5`.
- GHAS is enabled on `Repo1` and `Repo2`.
- Developer A and B are both active committers for `Repo5` as well.
- GHAS can be enabled on `Repo5` without consuming additional GHAS licenses.

## Use Cases

There are three primary use cases for this tool to help fulfill:

1. Increase the coverage of GHAS within your organization by enabling GHAS on repositories that do not require extra licenses.

    You enabled GHAS a few months ago as per your rollout plan and have consumed all the GHAS licenses you purchased. You think that there are new repositories that were created, some repositories that were migrated in the meantime, where GHAS can be enabled without consuming extra licenses. You want to find those repositories and enable GHAS on them.

2. Optimize the coverage of GHAS within your organization with the current number of licenses and find the maximum coverage that can be achieved with the extra licenses available.

    You enabled GHAS a few months ago on your business-critical repositories, and you have N number of GHAS licenses still available. You want to find the repositories that can be enabled with the current licenses but also find the longest combinations of repositories that you can enable with the extra licenses available.

3. Find which repositories to start GHAS enablement in an organization to achieve the maximum coverage with the licenses available.

    You have purchased GHAS licenses, and you are planning your GHAS rollout. You know that you have more active committers than the number of purchased licenses, but you have one factor for the rollout, and that is to enable GHAS features on as many repositories as possible. You want to find the longest combination of repositories that you can enable with the licenses you have just bought and start your rollout.

## How the Script Works

The Python script takes the following inputs:

- Active committers: CSV report about active committers in your enterprise.
- GitHub Enterprise slug.
- GitHub Organization slug.
- GitHub Personal Access Token.
- Licenses available.
- Output file name.
- Output file format (Text or JSON).

It will first gather the list of all repositories in the enterprise or organization and their GHAS enabled status and create a list of objects. It will then parse the `Active committers` report and add the active committers to each repository object.

The script will then go through the list and find the repositories that will not require extra GHAS licenses to enable. It will categorize those into two groups: repositories whose active committers already consume a GHAS license and repositories that do not have active committers.

For the leftover repositories, if provided with a number of licenses available, it will find the longest combination of repositories that can be enabled within the available licenses limit.

It will then output the results into a file according to the output preferences.

### Active Committers

The maximum active committers report is a CSV file that contains the following columns:

```csv
User login,Organization / repository,Last pushed date
theztefan,thez-org/repo_name,2023-09-06
theztefan,thez-org/repo_name3,2023-10-06
theztefan,thez-org/repo_name2,2023-08-06
```

We will be using the Stafftools UI to generate this report.

### GHAS Status

We obtain the GHAS status for each repository in an organization by calling the `GET /orgs/{org}/repos` API endpoint.

## Output Report

The script will output a report that will contain the following information:

```text
# GHAS Activation and Coverage Optimization

------------------------------------------------------------
# Current Coverage

Total active committers: 2
Total repositories with GHAS: 1
Total repositories without GHAS: 46
Coverage: 2.13%
----------------------------------------
# Increase Coverage with Currently Consumed Licenses 

**Turning GHAS on following repositories will not consume additional licenses**
- Repositories with active committers already consume a GHAS license:
	 -  Repository: empty-one | GHAS Status: False | Last Pushed At: 2023-10-25T12:47:33Z | Active Committers: ['theztefan']
- Repositories without active committers:
	 -  Repository: ado-project-migration | GHAS Status: False | Last Pushed At: 2022-05-12T10:54:04Z | Active Committers: []
	 -  Repository: new-secret-demo | GHAS Status: False | Last Pushed At: 2023-02-24T16:31:40Z | Active Committers: []
	...
----------------------------------------
# Maximize Coverage with Additional Licenses 

**Turning GHAS on following repositories will consume 1 additional license**
- Combination of repositories to activate GHAS on:
	 -  Repository: hilly | GHAS Status: False | Last Pushed At: 2023-11-01T11:43:43Z | Active Committers: ['hill-scribes-0x', 'theztefan']

 New active committers that will consume a GHAS license:
	 -  hill-scribes-0x
----------------------------------------
# End State Coverage 

Total repositories with GHAS: 47
Coverage: 100.0%
```

or `JSON` for machine-parseable output to plug in your GHAS enablement automation script:

```json
{
    "all_repos": [
        {
            "name": "open-book",
            "org": "thez-org",
            "ghas_status": true,
            "pushed_at": "2023-10-25T12:25:07Z",
            "active_committers": [
                "theztefan"
            ]
        },
        {
            "name": "ado-project-migration",
            "org": "thez-org",
            "ghas_status": false,
            "pushed_at": "2022-05-12T10:54:04Z",
            "active_committers": []
        },
        ...
    ],
    "active_committers": [
        "theztefan",
        "hill-scribes-0x"
    ],
    "current_active_commiters": [
        "theztefan"
    ],
    "current_repos_with_ghas": [
        {
            "name": "open-book",
            "org": "thez-org",
            "ghas_status": true,
            "pushed_at": "2023-10-25T12:25:07Z",
            "active_committers": [
                "theztefan"
            ]
        }
    ],
    "current_repos_without_ghas_with_active_committers": [
        {
            "name": "empty-one",
            "org": "thez-org",
            "ghas_status": false,
            "pushed_at": "2023-10-25T12:

47:33Z",
            "active_committers": [
                "theztefan"
            ]
        }
    ],
    "current_repos_without_ghas_and_committers": [
        {
            "name": "ado-project-migration",
            "org": "thez-org",
            "ghas_status": false,
            "pushed_at": "2022-05-12T10:54:04Z",
            "active_committers": []
        },
        {
            "name": "new-secret-demo",
            "org": "thez-org",
            "ghas_status": false,
            "pushed_at": "2023-02-24T16:31:40Z",
            "active_committers": []
        },
       ...
    ],
    "new_active_committers": [
        "hill-scribes-0x"
    ],
    "max_coverage_repos": [
        {
            "name": "hilly",
            "org": "thez-org",
            "ghas_status": false,
            "pushed_at": "2023-11-01T11:43:43Z",
            "active_committers": [
                "hill-scribes-0x",
                "theztefan"
            ]
        },
        ...
    ]
}
```

## How to Run the Script

### Usage

```text
$ python3 main.py --help
usage: main.py [-h] --ac-report AC_REPORT [--enterprise ENTERPRISE] [--organization ORGANIZATION] [--output OUTPUT] [--output-format OUTPUT_FORMAT]
               [--token TOKEN] [--licenses LICENSES]

GHAS Activation and Coverage Activation

options:
  -h, --help            show this help message and exit
  --ac-report AC_REPORT
                        Path to the active committers report (required)
  --enterprise ENTERPRISE
                        Name of the enterprise
  --organization ORGANIZATION
                        Name of the organization
  --output OUTPUT       Path to the output file (default: 'report.md')
  --output-format OUTPUT_FORMAT
                        Output format - text or JSON (default: 'text')
  --token TOKEN         GitHub Personal Access Token (if not set in GITHUB_TOKEN environment variable)
  --licenses LICENSES   Number of (still) available GHAS licenses (default: 0)
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
- Run the script `python3 main.py --ac-report REPORT.csv --org ORG`

### Examples

1. Increase the coverage of GHAS within your organization by enabling GHAS on repositories that do not require extra licenses.

    ```shell
    python3 main.py --ac-report ghas_maximum_committers_thezorg.csv --org thez-org --output-format text --output report.md
    ```

2. Optimize the coverage of GHAS within your organization with the current number of licenses and find the maximum coverage that can be achieved with the extra licenses available.

    ```shell
    python3 main.py --ac-report ghas_maximum_committers_thezorg.csv --org thez-org --licenses 10  --output-format text --output report.md
    ```

    **Note: After enabling GHAS on the new repositories to get maximum coverage, you will want to re-run the script again to see if there are any new repositories that can be enabled with the new active committers.**

3. Find which repositories to start GHAS enablement in an organization to achieve the maximum coverage with the licenses available.

    ```shell
    python3 main.py --ac-report ghas_maximum_committers_thezorg.csv --org thez-org --licenses 600  --output-format json --output report.json
    ```
