import argparse
import logging
import os

from keep_diverse.texts_filter import TextsFilter
from keep_diverse.split_sets_mark import SplitSetsMark
from keep_diverse.knee_plot import KneePlot, DisplayKneeArgs
from keep_diverse.filtered_files_list import FilteredFilesList
from keep_diverse.filter_args import add_filter_args
from keep_diverse.lzma_algo import LZMAAlgo
from keep_diverse.poisson_metric import PoissonMetric


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-plot-path", type=str, required=True)
    parser.add_argument("--output-file-path", type=str, required=True)
    parser.add_argument("--dir", type=str, required=True)
    parser.add_argument("--max-files", type=int, required=True)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(description="Texts filter utility")
    add_arguments(parser)
    add_filter_args(parser)
    args = parser.parse_args()

    file_paths = [
        os.path.join(args.dir, name)
        for name in os.listdir(args.dir)
        if os.path.isfile(os.path.join(args.dir, name))
    ]

    TextsFilter(
        sets_split=SplitSetsMark(
            all_file_names=file_paths[: args.max_files],
            split_by=args.split_by,
            algo=LZMAAlgo(),
            metric=PoissonMetric(),
            relative_eps=args.relative_eps,
            max_tries=args.max_tries_per_filter_iteration,
            min_indices_count=args.min_indices_count,
            max_workers=args.max_workers,
        ),
        knee_plot=KneePlot(
            output_file=args.output_plot_path,
            display_knee_args=DisplayKneeArgs(
                total_files_count=args.max_files,
                split_by=args.split_by,
                relative_eps=args.relative_eps,
                max_tries=args.max_tries_per_filter_iteration,
                min_indices_count=args.min_indices_count,
                filter_rounds=args.filter_rounds,
            ),
        ),
        filtered_files_list=FilteredFilesList(
            output_file_path=args.output_file_path,
        ),
        max_iter=args.filter_rounds,
        max_workers=args.max_workers,
    ).process()


if __name__ == "__main__":
    main()
