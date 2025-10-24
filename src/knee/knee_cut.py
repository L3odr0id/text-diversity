import logging

from src.basic.counter_report import CounterReport
from src.knee.knee import Knee
from src.basic.simple_filter_report import SimpleFilterReport


class KneeCut:
    def __init__(
        self,
        knee_plot_path: str,
        counter_report_file: str,
        cut_result_file: str,
    ):
        self.knee_plot_path = knee_plot_path
        self.counter_report_file = counter_report_file
        self.cut_result_file = cut_result_file

    def cut(self):
        counter_report = CounterReport(output_file=self.counter_report_file)
        counter_report.load_counter()

        logging.info(f"Loaded counter report from {self.counter_report_file}")

        sorted_items = sorted(
            counter_report.counter.items(), key=lambda x: x[1], reverse=True
        )
        file_names, y_values = zip(*sorted_items)
        x_values = list(range(len(y_values)))

        knee = Knee(x_values=x_values, y_values=y_values)
        knee.draw(output_file=self.knee_plot_path)
        logging.info(f"Drawn knee plot to {self.knee_plot_path}")

        knee_point = knee.find_knee()
        knee_index = int(knee_point)
        logging.info(f"Found knee point: {knee_point}")

        files_right_of_knee = list(file_names[knee_index:])
        logging.info(f"Found {len(files_right_of_knee)} files right of knee")

        filter_result = SimpleFilterReport(self.cut_result_file, files_right_of_knee)
        filter_result.save()
        logging.info(f"Saved filter result to {self.cut_result_file}")
