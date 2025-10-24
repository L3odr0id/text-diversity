import argparse
import logging

from textdistance import LZMANCD

from src.sets_split.sets_split_mark import SetsSplitMark
from src.sets_split.split_plots import SplitPlots
from texts_diversity.files_list import FilesList
from texts_diversity.algo import Algo
from src.metrics.poisson_dist_metric import poisson_dist_metric
from src.knee.knee_cut import KneeCut


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(description="Texts filter utility")
    parser.add_argument("directory", help="Path to directory containing text files")
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to analyze"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--counter-report-file",
        type=str,
        required=True,
    )
    parser.add_argument("--split-by", type=int, required=True)
    parser.add_argument(
        "--max-iter",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--knee-plot-path",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--cut-result-file",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    directory = args.directory
    max_files = args.max_files

    files_list = FilesList(files_dir=directory, shuffle=False, max_files=max_files)

    lzma_algo = Algo("LZMANCD", LZMANCD().distance, color="royalblue")

    sets_split = SetsSplitMark(
        all_file_names=files_list.file_paths,
        split_by=args.split_by,
        algo=lzma_algo,
        metric=poisson_dist_metric(),
    )

    split_files_plots = SplitPlots(
        sets_split=sets_split,
        output_file=args.output_file,
        max_iter=args.max_iter,
        counter_report_file=args.counter_report_file,
    )

    split_files_plots.draw_all()

    KneeCut(
        knee_plot_path=args.knee_plot_path,
        counter_report_file=args.counter_report_file,
        cut_result_file=args.cut_result_file,
    ).cut()


main()
