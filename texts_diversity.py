import os
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass

from draw_plot import draw_all_plots


class Distances:
    def __init__(self, distance_func: Callable[[str, str], float], algo_name: str):
        self._algo_name = algo_name
        self._distance_func = distance_func
        self._data: Dict[Tuple[int, int], Optional[float]] = {}

    def add_dist(self, prev_text: str, prev_idx: int, cur_text: str, cur_idx: int) -> None:
        try:
            distance_value = self._distance_func(cur_text, prev_text)
        except Exception as e:
            print(f"Error calculating distance for pair ({prev_idx}, {cur_idx}): {e}")
            distance_value = None

        self._data[(prev_idx, cur_idx)] = distance_value

    def get_values(self) -> List[float]:
        return [v for v in self._data.values() if v is not None]

    def max_key(self) -> int:
        all_indices = set()
        for (i, j) in self._data.keys():
            all_indices.add(i)
            all_indices.add(j)

        if not all_indices:
            raise ValueError("No distance data available")

        return max(all_indices)

    def find_minimax_center(self) -> Tuple[int, float, Dict[int, float]]:
        """
        Find the most centered text using minimax method.
        """
        num_texts = self.max_key() + 1
        max_distances = {}

        # Max dist for all texts
        for i in range(num_texts):
            max_dist = 0.0
            for j in range(num_texts):
                if i != j:
                    if (j, i) in self._data and self._data[(j, i)] is not None:
                        dist = self._data[(j, i)]
                    elif (i, j) in self._data and self._data[(i, j)] is not None:
                        dist = self._data[(i, j)]
                    else:
                        raise ValueError(f"Distance ({i}, {j}) is not in storage")

                    max_dist = max(max_dist, dist)

            max_distances[i] = max_dist

        # Find the index with minimum maximum distance
        center_idx = min(max_distances.keys(), key=lambda k: max_distances[k])
        min_max_distance = max_distances[center_idx]

        return center_idx, min_max_distance, max_distances

    def distance(self, from_idx: int, to_idx: int) -> float:
        if (from_idx, to_idx) in self._data and self._data[(from_idx, to_idx)] is not None:
            distance_value = self._data[(from_idx, to_idx)]
        elif (to_idx, from_idx) in self._data and self._data[(to_idx, from_idx)] is not None:
            distance_value = self._data[(to_idx, from_idx)]
        else:
            raise ValueError(f"Distance ({from_idx}, {to_idx}) is not in storage")

        return distance_value

    def min_distance_from_last(self) -> Optional[float]:
        try:
            last_idx = self.max_key()
        except ValueError:
            return 0.0

        if last_idx == 0:
            return 0.0  # Only one text available

        min_distance = float("inf")
        for i in range(last_idx):
            try:
                distance = self.distance(last_idx, i)
                if distance < min_distance:
                    min_distance = distance
            except Exception:
                continue

        if min_distance == float("inf"):
            return 0.0
        return min_distance


@dataclass
class Algo:
    name: str
    func: Callable[[str, str], float]
    normalize: Optional[Callable[[List[float]], List[float]]] = None

@dataclass
class PlotConfig:
    name: str
    metric: Callable[[Distances], float]
    normalize_algorithms: List[str]  # List of algorithm names that need normalization

@dataclass
class AlgoResults:
    algo_name: str
    values: List[float]
    normalize_func: Optional[Callable[[List[float]], List[float]]] = None
    
    def get_normalized_values(self) -> List[float]:
        if self.normalize_func:
            return self.normalize_func(self.values)
        return self.values

class PlotSeries:
    def __init__(self, name: str):
        self.name = name
        self.algo_results: List[AlgoResults] = []
    
    def add_new_algo_result(self, algo_name: str, values: List[float], normalize_func: Optional[Callable[[List[float]], List[float]]] = None):
        self.algo_results.append(AlgoResults(algo_name, values, normalize_func))
    
    def get_algo_result(self, algo_name: str) -> AlgoResults:
        for algo_result in self.algo_results:
            if algo_result.algo_name == algo_name:
                return algo_result
        raise ValueError(f"Algorithm {algo_name} not found in plot series {self.name}")
    
    def add_value(self, algo_name: str, value: float):
        """Add a single value to the specified algorithm's results."""
        self.get_algo_result(algo_name).values.append(value)
    
    def get_plot_data(self, normalize_algorithms: List[str]) -> Dict[str, List[float]]:
        plot_data = {}
        for algo_result in self.algo_results:
            if algo_result.algo_name in normalize_algorithms:
                plot_data[algo_result.algo_name] = algo_result.get_normalized_values()
            else:
                plot_data[algo_result.algo_name] = algo_result.values
        return plot_data

def analyze_text_diversity(
    file_paths: List[str],
    plot_configs: List[PlotConfig],
    algos: List[Algo],
    output_file: str = "ncd_stats_plots.png",
    min_files_for_analysis: int = 10
) -> None:
    """
    Analyze text diversity using specified algorithms and plot series.

    Args:
        file_paths: List of full file paths to analyze
        plot_configs: List of PlotConfig objects defining what metrics to calculate
        algos: List of Algos
        output_file: Name of the output plot file
        min_files_for_analysis: Minimum number of files before starting analysis
    """
    distance_storages: List[Distances] = [
        Distances(distance_func=algo.func, algo_name=algo.name) for algo in algos
    ]

    x_values: list[int] = []

    # Create PlotSeries objects for each plot configuration
    plot_series_list = []
    for plot_cfg in plot_configs:
        plot_series = PlotSeries(plot_cfg.name)
        for algo in algos:
            plot_series.add_new_algo_result(algo.name, [], algo.normalize)
        plot_series_list.append(plot_series)

    file_contents = {}
    for file_idx, file_path in enumerate(file_paths):
        filename = os.path.basename(file_path)
        print(f"[+] Reading {filename}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_contents[filename] = f.read()

            # Calculate distances between current file and all previous files for each algorithm
            current_text = file_contents[filename]
            for prev_idx in range(file_idx):
                prev_filename = os.path.basename(file_paths[prev_idx])
                prev_text = file_contents[prev_filename]
                for storage in distance_storages:
                    storage.add_dist(prev_text, prev_idx, current_text, file_idx)

            if file_idx < min_files_for_analysis:
                continue
            # Calculate statistics for current iteration
            x_values.append(file_idx + 1)
            for storage in distance_storages:
                algo_name = storage._algo_name

                for i, plot_cfg in enumerate(plot_configs):
                    try:
                        value = plot_cfg.metric(storage)
                        plot_series_list[i].add_value(algo_name, value)

                        print(f'{plot_cfg.name} ({algo_name}): {value:.4f}')

                    except Exception as e:
                        print(f'Error calculating {plot_cfg.name} for {algo_name}: {e}')
                        plot_series_list[i].add_value(algo_name, float("nan"))

            if x_values:
                plots = []
                for i, plot_cfg in enumerate(plot_configs):
                    plot_data = plot_series_list[i].get_plot_data(plot_cfg.normalize_algorithms)
                    plots.append((plot_cfg.name, plot_data))
                
                draw_all_plots(x_values=x_values, plots=plots, title="Distance vs Number of Files", output_path=output_file)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
