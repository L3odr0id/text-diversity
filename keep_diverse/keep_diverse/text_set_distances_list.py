from typing import Dict, Tuple, Optional, List
import time
import logging

from .text_distance_algo import TextDistanceAlgo
from .texts_list import TextsList


class TextSetDistancesList:
    def __init__(self, algo: TextDistanceAlgo, texts: TextsList):
        self.algo = algo
        self.data: Dict[Tuple[int, int], Optional[float]] = {}
        self.texts_list = texts

    def init_texts(self, file_paths: List[str]):
        self.data = {}
        self.texts_list = TextsList()

        for file_path in file_paths:
            with open(file_path, "r", encoding="utf-8") as f:
                new_text = f.read()

            self.add_dist(self.texts_list.texts, new_text)

            self.texts_list.append(new_text)

        logging.info(f"Initialized TextSetDistancesList with {len(file_paths)} texts")

    def add_dist(self, old_texts: List[str], new_text: str):
        """
        Calculate distances with all previous texts
        """
        current_idx = len(old_texts)

        start_time = time.time()
        for prev_idx, prev_text in enumerate(old_texts):
            try:
                distance_value = self.algo.distance(new_text, prev_text)
            except Exception as e:
                print(
                    f"Error calculating distance for pair ({prev_idx}, {current_idx}): {e}"
                )
                distance_value = float("nan")

            self.data[(prev_idx, current_idx)] = distance_value
        elapsed_time = time.time() - start_time
        logging.debug(
            f"Algo {self.algo.name}. Computed distances to {current_idx} previous texts in {elapsed_time:.4f}s"
        )

    def copy(self):
        new_distances = TextSetDistancesList(self.algo, self.texts_list)
        new_distances.data = self.data.copy()
        return new_distances

    # def values_without_idxs(self, text_ids: List[int]) -> List[float]:
    #     return [
    #         self.data[(i, j)]
    #         for i, j in self.data.keys()
    #         if i not in text_ids and j not in text_ids
    #     ]

    def values(self) -> List[float]:
        return list(self.data.values())

    def remove_list(self, text_ids: List[int]):
        keys_to_remove = []
        for key in self.data.keys():
            i, j = key
            if i in text_ids or j in text_ids:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.data.pop(key, None)
