import argparse

from textdistance import LZMANCD

from src.sets_split.sets_split import SetsSplit
from src.sets_split.split_filter_results import SplitFilterResults
from texts_diversity.files_list import FilesList
from texts_diversity.algo import Algo
from src.metrics.poisson_dist_metric import poisson_dist_metric
import logging


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
    parser.add_argument("--split-by", type=int, required=True)
    args = parser.parse_args()

    directory = args.directory
    max_files = args.max_files

    files_list = FilesList(files_dir=directory, shuffle=False, max_files=max_files)

    lzma_algo = Algo("LZMANCD", LZMANCD().distance, color="royalblue")

    sets_split = SetsSplit(
        all_file_names=files_list.file_paths,
        split_by=args.split_by,
        algo=lzma_algo,
        metric=poisson_dist_metric(),
    )

    split_filter_results = SplitFilterResults(sets_split=sets_split)

    split_filter_results.process(output_file_path=args.output_file)


if __name__ == "__main__":
    main()
