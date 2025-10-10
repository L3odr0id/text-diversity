from typing import List


class BigToSmallerSetsSplit:
    def __init__(self, total_files_count: int, split_by: int):
        self.total_files_count = total_files_count
        self.split_by = split_by

    def just_do_it(self, file_paths: List[str], process_one_set_func):
        current_file_paths = file_paths.copy()
        stage = 0

        while len(current_file_paths) > self.split_by:
            current_count = len(current_file_paths)
            num_groups = (current_count + self.split_by - 1) // self.split_by

            print(
                f"Stage {stage}: Processing {current_count} files in {num_groups} groups of {self.split_by}"
            )

            filtered_files = []

            for group_idx in range(num_groups):
                start_idx = group_idx * self.split_by
                end_idx = min(start_idx + self.split_by, current_count)

                print(
                    f"  Processing group {group_idx + 1}/{num_groups}: files {start_idx}-{end_idx}"
                )

                group_filtered_files = process_one_set_func(
                    start_idx, end_idx, stage, current_file_paths
                )
                filtered_files.extend(group_filtered_files)

            current_file_paths = filtered_files
            print(f"Stage {stage} complete: {len(filtered_files)} files remaining")
            stage += 1

        if len(current_file_paths) > 0:
            process_one_set_func(0, len(current_file_paths), stage, current_file_paths)
