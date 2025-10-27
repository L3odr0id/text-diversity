import argparse
import time
from typing import List

from textdistance import LZMANCD
import matplotlib.pyplot as plt

from texts_diversity.files_list import FilesList
from texts_diversity.algo import Algo
from utils import cis_same_metric
from src.metrics.poisson_dist_metric import poisson_dist_metric
from src.sets_split.sets_split_mark import SetsSplitMark
from texts_diversity.utils import save_plot_safely


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        type=str,
        default="generated",
        help="Directory containing input files (default: generated)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Maximum number of files to process (default: 200)",
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default="timing_experiment.svg",
        help="Path for output plot file (default: timing_experiment.svg)",
    )
    return parser.parse_args()


def run_timing_experiment(dir_path: str, max_files_list: List[int], output_plot: str):
    lzma_algo = Algo("LZMANCD", LZMANCD().distance, color="royalblue")

    file_counts = []
    times = []

    for max_files in max_files_list:
        print(f"Processing {max_files} files...")

        files_list = FilesList(files_dir=dir_path, shuffle=False, max_files=max_files)

        calc_infos = cis_same_metric(
            algos=[lzma_algo],
            metric=poisson_dist_metric,
        )

        old_texts = []

        def process_file(file_path: str):
            with open(file_path, "r", encoding="utf-8") as f:
                new_text = f.read()

            for calc_info in calc_infos:
                calc_info.distances.add_dist(old_texts, new_text)

            old_texts.append(new_text)

        start_time = time.time()
        files_list.for_each(process_file)

        sets_split_mark = SetsSplitMark(
            all_file_names=files_list.file_paths,
            split_by=max_files,
            algo=lzma_algo,
            metric=poisson_dist_metric(),
        )
        files_to_remove = sets_split_mark.filter_files()

        end_time = time.time()
        elapsed_time = end_time - start_time

        file_counts.append(max_files)
        times.append(elapsed_time)

        print(
            f"Completed {max_files} files in {elapsed_time:.2f} seconds (filtered {len(files_to_remove)} files)"
        )

        fig = plt.figure(figsize=(10, 6))
        plt.plot(file_counts, times, marker="o")
        plt.xlabel("Number of Files")
        plt.ylabel("Time (seconds)")
        plt.title("Filtering time vs number of files")
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        save_plot_safely(fig, output_plot)

    return file_counts, times


args = parse_args()

file_counts_to_test = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250]

run_timing_experiment(
    dir_path=args.dir,
    max_files_list=file_counts_to_test,
    output_plot=args.output_plot,
)
