# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based tool that analyzes GitHub Advanced Security (GHAS) license utilization within GitHub organizations and enterprises. The tool helps optimize GHAS coverage by identifying repositories that can be enabled without consuming additional licenses and finding optimal combinations of repositories to maximize coverage with available licenses.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Set GitHub token
export GITHUB_TOKEN=<your-token>
```

### Running the Application
```bash
# Basic usage with organization
python3 main.py --organization ORG_NAME

# With active committers CSV report (preferred method)
python3 main.py --ac-report report.csv --organization ORG_NAME

# With available licenses for optimization
python3 main.py --organization ORG_NAME --licenses 10

# Enterprise-wide analysis
python3 main.py --enterprise ENTERPRISE_NAME --licenses 100

# Output formats
python3 main.py --organization ORG_NAME --output-format json --output report.json
python3 main.py --organization ORG_NAME --output-format text --output report.md
```

### Testing
```bash
# Run all tests with custom test runner
python3 -m unittest discover tests/ -v

# Run specific test files
python3 tests/test_max_coverage.py
python3 tests/test_active_committers.py

# The tests use a custom colorized test runner defined in tests/custom_test_runner.py
```

### Code Quality
The repository has GitHub Actions configured for:
- CodeQL security analysis (runs on push/PR to main)
- Dependency review (runs on PRs)

## Code Architecture

### Core Module Structure

**main.py**
- Entry point that orchestrates the entire workflow
- Parses CLI arguments, coordinates data gathering, and generates reports

**github.py** - GitHub API Integration
- `add_active_committers()`: Processes CSV reports or fetches via GraphQL API
- `get_ghas_status_for_repos()`: Retrieves repository GHAS status via REST API and automatically filters out archived repositories
- `get_active_committers_in_last_90_days()`: GraphQL queries for commit history
- `get_orgs_in_ent()`: Enterprise organization discovery
- `handle_rate_limit()`: Intelligent rate limiting with exponential backoff
- Uses ThreadPoolExecutor for concurrent API calls (MAX_WORKERS = 5)

**models.py** - Data Models
- `Repository`: Core data structure with GHAS status, visibility, and active committers
- `Report`: Comprehensive report structure with calculated properties for coverage metrics

**report.py** - Analysis Engine
- `generate_ghas_coverage_report()`: Categorizes repositories based on GHAS status and committers
- `find_combination_with_max_repositories_greedy()`: Optimization algorithm for license allocation
- `find_combination_with_max_repositories()`: Brute-force algorithm for smaller datasets
- `write_report()`: Outputs text or JSON formatted reports

**helpers.py** - Utilities
- Argument parsing with validation
- Logging configuration
- Environment variable handling

### Key Business Logic

The tool categorizes repositories into distinct groups:

1. **Current GHAS Repos**: Already have GHAS enabled
2. **Free Activation Candidates**:
   - Repos with committers already consuming GHAS licenses
   - Public repositories (no license required)
   - Private/internal repos without active committers
3. **License-Required Repos**: Private repos with new active committers

The optimization algorithm uses a greedy approach to maximize repository coverage within license constraints, prioritizing repositories with the most unique new committers.

### Data Flow

1. **Discovery**: Fetch organizations → repositories → GHAS status (archived repositories automatically filtered out)
2. **Committer Analysis**: Process CSV report or query GraphQL API for active committers (90-day window)
3. **Categorization**: Group repositories by activation requirements
4. **Optimization**: Find optimal combinations for available licenses
5. **Reporting**: Generate text/JSON output with coverage metrics

### Rate Limiting Strategy

The GitHub API integration implements sophisticated rate limiting:
- Monitors `X-RateLimit-Remaining` headers
- Proactive slowdown when <50 requests remaining
- Thread-safe rate limit handling with locks
- Respects `Retry-After` headers and reset timestamps
- 1-second base delay between all requests

### Testing Architecture

- Custom test runner with colorized output and execution timing
- Unit tests for the optimization algorithms with randomized test data
- Tests focus on the core business logic rather than API integration
- Uses `unittest` framework with custom `CustomTextTestRunner`

## Key Configuration

### Required Permissions
GitHub Personal Access Token needs:
- `repo` scope for repository access
- `admin:org` for organization-level operations
- `admin:enterprise` for enterprise-level operations

### API Usage Patterns
- REST API for repository metadata and GHAS status
- GraphQL API for active committer analysis (when CSV unavailable)
- Prefers CSV reports over GraphQL for performance and reliability
- Excludes `dependabot[bot]` from active committer counts
- Only analyzes private/internal repositories for committer data (public repos don't require licenses)

## Output Formats

The tool generates detailed reports showing:
- Current coverage metrics and active committer counts
- Repositories eligible for free GHAS activation
- Optimal repository combinations for available licenses
- New committers that would consume additional licenses
- Final coverage projections

Reports available in both human-readable text format and machine-parseable JSON for automation integration.
