import argparse
import os


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--split-by",
        type=int,
        default=50,
    )
    parser.add_argument(
        "--relative-eps",
        type=float,
        default=0.00001,
    )
    parser.add_argument(
        "--max-tries-per-filter-iteration",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--min-indices-count",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--filter-rounds",
        type=int,
        default=100,
    )
