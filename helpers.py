import argparse
import os


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="GHAS activation and coverage activation"
    )
    parser.add_argument(
        "--ac-report",
        type=str,
        help="Path to the active committers report",
        required=True,
    )
    parser.add_argument(
        "--enterprise", type=str, help="Name of the enterprise", required=False
    )
    parser.add_argument(
        "--organization", type=str, help="Name of the organization", required=False
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to the output file",
        required=False,
        default="report.txt",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        help="Output format - text or json",
        required=False,
        default="text",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub Personal Access Token (if not set in GITHUB_TOKEN envrionment variable)",
        required=False,
    )
    args = parser.parse_args()

    if args.enterprise is None and args.organization is None:
        parser.error("Either --enterprise or --organization must be provided.")

    token = os.getenv("GITHUB_TOKEN") or args.token
    if token is None:
        parser.error(
            "Either GITHUB_TOKEN environment variable or --token must be provided."
        )

    return args, token
