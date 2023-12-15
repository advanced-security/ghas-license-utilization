from dotenv import load_dotenv
from github import *
from report import *
from helpers import *

load_dotenv()
logger = get_logger()


def main():
    # Parse arguments provided
    args, token = parse_arguments()

    # Gather all data needed for the report - all orgs in the enterprise, repositories in orgs and active committers in repositories
    orgs_in_ent = get_organizations(args, token)
    logger.info(f"Number of organizations to process: {len(orgs_in_ent)}")
    total_repositories = process_organizations(orgs_in_ent, token)

    logger.info(f"Adding active committers to {len(total_repositories)} repositories")
    add_active_committers(args.ac_report, total_repositories, token)

    # Generate report and print report
    logger.info(f"Generating report...")
    results = generate_max_coverage_report(total_repositories, args.licenses)
    write_report(results, args.output, args.output_format)


if __name__ == "__main__":
    main()
