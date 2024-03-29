import argparse
import os
import logging


def get_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="GHAS activation and coverage activation"
    )
    parser.add_argument(
        "--ac-report",
        type=str,
        help="Path to the active committers report",
        required=False,
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
        help="Path to the output file (default: 'report.md')",
        required=False,
        default="report.md",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        help="Output format - text or json (default: 'text')",
        required=False,
        default="text",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub Personal Access Token (if not set in GITHUB_TOKEN environment variable)",
        required=False,
    )
    parser.add_argument(
        "--licenses",
        type=int,
        help="Number of (still) available GHAS licenses (default: 0)",
        required=False,
        default=0,
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
