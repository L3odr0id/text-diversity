from dataclasses import dataclass
from typing import Callable


@dataclass
class Algo:
    name: str
    func: Callable[[str, str], float]


@dataclass
class CompressAlgo:
    name: str
    func: Callable[[str], bytes]
