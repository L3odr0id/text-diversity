from typing import List


class FilterResult:
    def __init__(self, file_paths: List[str]):
        self.content = "\n".join(list(sorted(file_paths)))

    def save(self, report_pattern: str, range_start: int, range_end: int, stage: int):
        res_file_name = (
            f"{report_pattern}_range({range_start}-{range_end})_stage({stage}).txt"
        )
        with open(res_file_name, "w") as f:
            f.write(self.content)

        print(f"[FilterResult] Saved to {res_file_name}")
