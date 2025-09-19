from datetime import datetime
from texts_diversity.plots_list import PlotsList
from texts_diversity.files_list import FilesList


class TextsDiversity:
    def __init__(
        self, files_list: FilesList, plots_list: PlotsList, min_files_for_analysis: int
    ):
        self.files_list = files_list
        self.plots_list = plots_list
        self.texts = []
        self.min_files_for_analysis = min_files_for_analysis
        self.start_datetime = None

    def process_file(self, new_file_content: str):
        self.texts.append(new_file_content)

        for plot_config in self.plots_list.configs:
            for td in plot_config.texts_distances:
                td.add_dist(self.texts, new_file_content)

        if len(self.texts) < self.min_files_for_analysis:
            return

        self.plots_list.add_x_value(len(self.texts))
        self.plots_list.add_y_values()
        self.plots_list.draw()

        self.print_elapsed_time()

    def print_elapsed_time(self):
        if self.start_datetime:
            elapsed = datetime.now() - self.start_datetime
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            print(
                f"[{hours:02d}h - {minutes:02d}m - {seconds:02d}s] Printed plot for {len(self.texts)} texts to {self.plots_list.output_file}"
            )
        else:
            print("Start datetime is not set")

    def set_start_datetime(self):
        self.start_datetime = datetime.now()

    def draw_plots(self):
        self.set_start_datetime()
        self.files_list.for_each(self.process_file)
