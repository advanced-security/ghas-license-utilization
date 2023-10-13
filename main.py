import logging
from dotenv import load_dotenv
from github import *
from report import *
from helpers import *

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_organizations(args, token):
    orgs_in_ent = []
    if not args.enterprise:
        orgs_in_ent.append(args.organization)
    else:
        orgs_in_ent = get_orgs_in_ent(args.enterprise, token)
    return orgs_in_ent


def process_organizations(orgs_in_ent, token):
    total_repositories = []
    for i, org in enumerate(orgs_in_ent, start=1):
        logger.info(f"[{i}/{len(orgs_in_ent)}] Processing organization: {org}")
        total_repositories.extend(get_ghas_status_for_repos(org, token))
    return total_repositories


def main():
    # Parse arguments provided
    args, token = parse_arguments()

    # Gather all data needed for the report - all orgs in the enterprise, repositories in orgs and active committers in repositories
    orgs_in_ent = get_organizations(args, token)
    logger.info(f"Number of organizations to process: {len(orgs_in_ent)}")

    total_repositories = process_organizations(orgs_in_ent, token)
    logger.info(f"Adding active committers to {len(total_repositories)} repositories")
    add_active_committers(args.ac_report, total_repositories)

    # Generate report and print report
    logger.info(f"Generating report...")
    results = generate_ghas_coverage_report(total_repositories)

    write_report(results, args.output, args.output_format)
    logger.info(f"Report written to: {args.output}")


if __name__ == "__main__":
    main()
