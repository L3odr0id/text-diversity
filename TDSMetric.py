import time
from typing import List

from texts_diversity.algo import CompressAlgo
from texts_diversity.iterative_metric import (
    IterativeMetric,
    IterativeMetricCalculationResult,
)


class TDSMetric(IterativeMetric):
    def __init__(self, algo: CompressAlgo):
        super().__init__("TDS Metric")
        self.algo = algo

    def NCD1(self, texts: List[str]) -> float:
        start_time = time.time()

        c_X = len(self.algo.func("".join(texts)))
        # get min of C(X)
        compressed_lengths = [len(self.algo.func(text)) for text in texts]
        min_length = min(compressed_lengths)
        # For each x in texts, remove x, compress the rest, get C(X\{x})
        c_x_removed = []
        for i in range(len(texts)):
            texts_without_x = texts[:i] + texts[i + 1 :]
            compressed = self.algo.func("".join(texts_without_x))
            c_x_removed.append(len(compressed))
        max_c_x_removed = max(c_x_removed)
        value = (c_X - min_length) / max_c_x_removed

        elapsed = time.time() - start_time
        print(f"TDSMetric. NCD1: elapsed {elapsed:.4f}s for {len(texts)} texts")
        return value

    def calc(self, texts: List[str]) -> IterativeMetricCalculationResult:
        max_value = float("-inf")
        best_texts = texts
        for i in range(len(texts)):
            texts_without_i = texts[:i] + texts[i + 1 :]
            value = self.NCD1(texts_without_i)
            if value > max_value:
                max_value = value
                best_texts = texts_without_i
        value = max_value
        return IterativeMetricCalculationResult(
            value=value,
            texts=best_texts,
            finished=len(best_texts) <= 2,
        )
