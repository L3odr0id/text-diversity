import argparse
import os


def add_runner_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--runner-main",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--errors-report",
        type=str,
        default="errors_report.json",
    )
    parser.add_argument(
        "--verilog-out-name",
        type=str,
        default="a.out",
    )
    parser.add_argument(
        "--gh-pages-dir",
        type=str,
        required=True,
    )
