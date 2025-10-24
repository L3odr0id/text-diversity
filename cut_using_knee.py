import argparse
import logging

from src.knee.knee_cut import KneeCut


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(description="Texts filter utility")
    parser.add_argument(
        "--counter-report-file",
        type=str,
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

    KneeCut(
        knee_plot_path=args.knee_plot_path,
        counter_report_file=args.counter_report_file,
        cut_result_file=args.cut_result_file,
    ).cut()


main()
