# GHAS Activation and Coverage Optimization

The purpose of this project is to optimize the utilization of GHAS (GitHub Advanced Security) licenses within your organization. GHAS operates on a licensing model based on active committers. Each active committer consumes one GHAS license, meaning GHAS can be enabled for any repository to which this committer contributes.

**Example:**

- Developer A contributes to 3 repositories - `Repo1`, `Repo2`, `Repo5`.
- Developer B contributes to 2 repositories - `Repo2`, `Repo5`.
- GHAS is enabled on `Repo1` and `Repo2`.
- Both Developer A and B are active committers to `Repo5`.
- Enabling GHAS on `Repo5` does not require additional GHAS licenses.

## Use Cases

This tool assists in three primary practical scenarios:

1. **Increase GHAS Coverage:**
   You've already enabled GHAS a few months ago according to your rollout plan and have utilized all the GHAS licenses you purchased. Now, you believe that new repositories have been created or migrated, where GHAS can be enabled without needing additional licenses. Your goal is to identify these repositories and activate GHAS on them.

2. **Optimize GHAS Coverage:**
   A few months ago, you activated GHAS on your business critical repositories and still have a certain number of GHAS licenses available. Your objective is to discover repositories that can be activated with the existing licenses and also to find the most extensive combinations of repositories that can be enabled with the extra licenses you have.

3. **Strategic GHAS Rollout:**
   Having purchased GHAS licenses, you are now planning your GHAS rollout. You are aware that the number of active committers exceeds the number of licenses you have. However, your primary focus is to enable GHAS features on as many repositories as possible. You aim to identify the most extensive combination of repositories that can be enabled with the licenses you've acquired and initiate your rollout.

## How the Script Works

The Python script processes the following inputs:

- Active committers:
    1. Parsing a CSV report on maximum active committers in your enterprise, or [preferably]
    2. Finding active committers via the GraphQL API (experimental and slower).
- GitHub Enterprise slug.
- GitHub Organization slug.
- GitHub Personal Access Token.
- Number of available GHAS licenses.
- Output file name.
- Output file format (Text or JSON).

The script first compiles a list of all repositories within the enterprise and/or organization(s), including their GHAS status. It then processes the `Max active committers` report or fetches active committers for each repository using the GraphQL API, adding this data to each repository object.

Next, the script identifies repositories that can be enabled with GHAS without requiring additional licenses, categorizing them into three groups:

- Repositories whose active committers already consume a GHAS license.
- Public repositories not requiring a GHAS license for enablement.
- Repositories without active committers.

For remaining repositories, given the number of available licenses, the script determines the longest combination of repositories that can be enabled within the license limit.

Finally, it outputs the results in the chosen file format.

### Active Committers

The script uses the `Max active committers` report or the GraphQL API to obtain the list of active committers for each repository. The maximum active committers report is preferred way as it runs the script faster and is more reliable. The GraphQL API is experimental and slower but can be used if the `Max active committers` report is not available.

```csv
User login,Organization / repository,Last pushed date
theztefan,thez-org/repo_name,2023-09-06
theztefan,thez-org/repo_name3,2023-10-06
theztefan,thez-org/repo_name2,2023-08-06
```

### GHAS Status

The GHAS status for each repository in an organization is obtained by calling the GET /orgs/{org}/repos API endpoint.

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
    "current_repos_without_ghas_and_public": [
        {
            "name": "go-gin-example",
            "org": "thez-org",
            "ghas_status": false,
            "visibility": "public",
            "pushed_at": "2023-07-03T08:59:02Z",
            "active_committers": []
        },
        {
            "name": "rails-ex",
            "org": "thez-org",
            "ghas_status": false,
            "visibility": "public",
            "pushed_at": "2023-03-03T16:00:58Z",
            "active_committers": []
        },
        {
            "name": "rails-react-typescript-docker-example",
            "org": "thez-org",
            "ghas_status": false,
            "visibility": "public",
            "pushed_at": "2023-03-10T12:15:50Z",
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
usage: main.py [-h] [--ac-report AC_REPORT] [--enterprise ENTERPRISE] [--organization ORGANIZATION] [--output OUTPUT] [--output-format OUTPUT_FORMAT] [--token TOKEN] [--licenses LICENSES]

GHAS activation and coverage activation

options:
  -h, --help            show this help message and exit
  --ac-report AC_REPORT
                        Path to the active committers report
  --enterprise ENTERPRISE
                        Name of the enterprise
  --organization ORGANIZATION
                        Name of the organization
  --output OUTPUT       Path to the output file (default: 'report.md')
  --output-format OUTPUT_FORMAT
                        Output format - text or json (default: 'text')
  --token TOKEN         GitHub Personal Access Token (if not set in GITHUB_TOKEN envrionment variable)
  --licenses LICENSES   Number of (still) available GHAS licenses (default: 0)
```

You would need to provide:

- `--ac-report` with the path to the Max Active Committers report. If left empty, the script will gather the data from the GraphQL API.
- `--organization` and/or `--enterprise` parameters to specify the scope of the script.

### Prerequisites

- Python 3.9 or later.
- Personal Access Token (PAT) with permissions depending on the scope you plan to run it - `repo`, `admin:org`, `admin:enterprise`.
- Active committers report saved locally.

### Running

1. Create a virtual environment: `python3 -m venv venv`.
2. Activate your virtual environment: `source venv/bin/activate`.
3. Install dependencies: `pip3 install -r requirements.txt`.
4. Set the GitHub PAT in the `GITHUB_TOKEN` environment variable: `export GITHUB_TOKEN=<token>`.
5. Run the script: `python3 main.py --ac-report REPORT.csv --org ORG`.

### Examples

1. **Increase the coverage of GHAS** within your organization by enabling GHAS on repositories that do not require extra licenses.

    ```shell
    # With Active Commiters Report available
    python3 main.py --ac-report ghas_maximum_committers_thezorg.csv --org thez-org --output-format text --output report.md   

    # Gather Active Committers from API
    python3 main.py --org thez-org --output-format text --output report.md 
    ```

2. **Optimize the coverage of GHAS** within your organization with the current number of licenses and find the maximum coverage that can be achieved with the extra licenses available.

    ```shell
    # With Active Commiters Report available
    python3 main.py --ac-report ghas_maximum_committers_thezorg.csv --org thez-org --licenses 10  --output-format text --output report.md   
    
    # Gather Active Committers from API
    python3 main.py --org thez-org --licenses 10  --output-format text --output report.md   
    ```

    **Note: After enabling GHAS on the new repositories to get maximum coverage, you will want to re-run the script again to see if there are any new repositories that can be enabled with the new active committers. Currently, the script doesn't calculate the new coverage after enabling GHAS on the new repositories.**

3. **Strategic GHAS rollout** by finding the repositories to achieve the maximum coverage with the licenses available.

    ```shell
    # With Active Commiters Report available
    python3 main.py --ac-report ghas_maximum_committers_thezorg.csv --org thez-org --licenses 600  --output-format json --output report.json    

    # Gather Active Commiters from API
    python3 main.py --org thez-org --licenses 600  --output-format json --output report.json    
    ```
