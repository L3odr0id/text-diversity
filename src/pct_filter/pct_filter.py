from typing import List, Tuple
import logging
import random
import time

from texts_diversity.calc_info import CalcInfo


class PctFilter:
    def __init__(
        self,
        initial_indices: List[int],
        relative_eps: float,
        max_tries: int,
        intial_metric_value: float,
        min_indices_count: int,
        calc_info: CalcInfo,
    ):
        self.initial_indices = initial_indices
        self.current_idxs = initial_indices
        self.current_metric_value = intial_metric_value
        self.relative_eps = relative_eps
        self.max_tries = max_tries
        self.min_indices_count = min_indices_count
        self.is_finished = False
        self.iteration = 0
        self.calc_info = calc_info

    def remove_idxs_attempt(
        self,
        current_idxs: List[int],
        removal_pct: float,
        current_value: float,
        num_to_remove: int,
        attempt: int,
    ) -> Tuple[List[int], float] | None:
        indices_to_remove = random.sample(current_idxs, num_to_remove)
        remaining_indices = [
            idx for idx in current_idxs if idx not in indices_to_remove
        ]

        start_time = time.time()
        new_value = self.metric_value_without_idxs(indices_to_remove)
        elapsed_time = time.time() - start_time
        logging.debug(
            f"Metric {self.calc_info.metric.name} x algo {self.calc_info.distances.algo.name} calculation took {elapsed_time:.4f} seconds."
        )

        metric_change = current_value - new_value
        eps_change = self.relative_eps * current_value
        info = f"Try {attempt + 1}. Metric {self.calc_info.metric.name} x algo {self.calc_info.distances.algo.name}. Remove {removal_pct * 100}% ({num_to_remove}). Old {current_value}. New {new_value}. Diff: {metric_change}. relative_eps: {self.relative_eps}. Metric change: {metric_change}. relative_eps*prev_value: {eps_change}.  Is metric changed less than eps: {metric_change <= eps_change}"

        if metric_change <= eps_change:
            logging.info(f"Attempt succeeded. {info}")
            return remaining_indices, new_value
        else:
            logging.debug(f"Attempt failed. {info}")
            return None

    def try_to_remove_idxs(
        self,
        current_idxs: List[int],
        removal_pct: float,
        current_value: float,
    ) -> Tuple[List[int], float, bool]:
        texts_count = len(current_idxs)
        num_to_remove = int(texts_count * removal_pct)

        if (
            texts_count <= 2
            or num_to_remove < 1
            or removal_pct == 1.0
            or texts_count - num_to_remove < self.min_indices_count
        ):
            return current_idxs, current_value, True

        for attempt in range(self.max_tries):
            result = self.remove_idxs_attempt(
                current_idxs, removal_pct, current_value, num_to_remove, attempt
            )
            if result is not None:
                return result[0], result[1], False

        logging.debug(f"All attempts failed")
        return current_idxs, current_value, False

    def search_for_removal_percentage(
        self,
        initial_indices: List[int],
        initial_metric_value: float,
    ) -> Tuple[List[int], float]:
        logging.debug(f"Start searching for removal percentage.")
        left = 0
        right = 100

        tmp_new_indicies = initial_indices
        tmp_new_metric_value = initial_metric_value

        while left <= right:
            mid = (left + right) // 2
            remove_pct = mid / 100

            logging.debug(f"Mid: {mid}. Left: {left}. Right: {right}.")

            new_remaining_indices, new_value, isFinished = self.try_to_remove_idxs(
                initial_indices,
                remove_pct,
                initial_metric_value,
            )

            if isFinished:
                logging.debug(f"Break.")
                return (tmp_new_indicies, tmp_new_metric_value)

            removed_successfully = len(new_remaining_indices) < len(initial_indices)

            if removed_successfully:
                tmp_new_indicies = new_remaining_indices
                tmp_new_metric_value = new_value
                logging.debug(
                    f"Removed {mid}%. New value: {new_value}. New texts count: {len(new_remaining_indices)}."
                )
                left = mid + 1
            else:
                logging.debug(f"Did not removed {mid}%.")
                right = mid - 1

        logging.debug(
            f"Finished. Removed {mid}%. New value: {tmp_new_metric_value}. New texts count: {len(tmp_new_indicies)}."
        )
        return (tmp_new_indicies, tmp_new_metric_value)

    def iterate(self):
        if self.is_finished:
            return

        self.iteration += 1

        new_remaining_indices, new_value = self.search_for_removal_percentage(
            self.current_idxs, self.current_metric_value
        )
        successfuly_shrinked = len(new_remaining_indices) < len(self.current_idxs)

        logging.info(
            f"Iter {self.iteration}. Successfully shrinked: {successfuly_shrinked}. Old value: {self.current_metric_value} New value: {new_value}. Old count: {len(self.current_idxs)} New count: {len(new_remaining_indices)}."
        )

        if successfuly_shrinked:
            self.current_idxs = new_remaining_indices
            self.current_metric_value = new_value
        else:
            self.is_finished = True

    def metric_value_without_idxs(self, idxs_to_remove: List[int]) -> float:
        return self.calc_info.value_without_idxs(idxs_to_remove)
