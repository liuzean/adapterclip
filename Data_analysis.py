"""Compare result tables between two revised-content markers in a log file."""

import argparse
import logging
import os
import re
from datetime import datetime


NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
K_SHOTS_RE = re.compile(r"k_shots=(\d+)")


def build_logger(save_path, log_file):
    os.makedirs(save_path, exist_ok=True)
    logger = logging.getLogger("result_comparison")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(levelname)s: %(message)s",
        datefmt="%y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(os.path.join(save_path, log_file), mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def read_lines(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()


def extract_k_shots(line):
    match = K_SHOTS_RE.search(line)
    if not match:
        return None
    return int(match.group(1))


def is_table_header(line):
    if not line.lstrip().startswith("|"):
        return False
    cells = split_pipe_row(line)
    return bool(cells) and cells[0].strip() == "Name"


def find_table_after_marker(lines, marker_line_idx):
    table_start = None
    for idx in range(marker_line_idx + 1, len(lines)):
        if is_table_header(lines[idx]):
            table_start = idx
            break

    if table_start is None:
        raise ValueError(f"No pipe table found after line {marker_line_idx + 1}")

    table_lines = []
    for idx in range(table_start, len(lines)):
        line = lines[idx].strip()
        if not line.startswith("|"):
            break
        table_lines.append(line)

    if len(table_lines) < 3:
        raise ValueError(f"Pipe table after line {marker_line_idx + 1} has fewer than 3 rows")
    return table_lines


def collect_tables_by_marker(lines, marker):
    tables = {}
    marker_pattern = re.compile(r"^\s*" + re.escape(marker) + r"(?:\s+|$)")
    for idx, line in enumerate(lines):
        if not marker_pattern.match(line):
            continue
        k_shots = extract_k_shots(line)
        if k_shots is None:
            continue
        tables[k_shots] = {
            "line": idx + 1,
            "table": find_table_after_marker(lines, idx),
        }
    return tables


def split_pipe_row(row):
    parts = row.strip().split("|")
    if len(parts) >= 2 and parts[0] == "" and parts[-1] == "":
        return parts[1:-1]
    return parts


def is_number_cell(cell):
    return NUMBER_RE.match(cell.strip()) is not None


def format_diff(next_value, previous_value):
    return f"{next_value - previous_value:+.1f}"


def center_like(value, previous_cell, next_cell):
    width = max(len(previous_cell), len(next_cell), len(value) + 2)
    return value.center(width)


def compare_tables(previous_table, next_table):
    if len(previous_table) != len(next_table):
        raise ValueError("Compared tables have different row counts")

    output_lines = []
    for row_idx, (previous_row, next_row) in enumerate(zip(previous_table, next_table)):
        previous_cells = split_pipe_row(previous_row)
        next_cells = split_pipe_row(next_row)
        if len(previous_cells) != len(next_cells):
            raise ValueError(f"Compared tables have different column counts at row {row_idx + 1}")

        if row_idx < 2:
            output_lines.append(next_row)
            continue

        output_cells = []
        for col_idx, (previous_cell, next_cell) in enumerate(zip(previous_cells, next_cells)):
            if col_idx == 0:
                output_cells.append(next_cell)
                continue

            if is_number_cell(previous_cell) and is_number_cell(next_cell):
                diff_text = format_diff(float(next_cell.strip()), float(previous_cell.strip()))
                output_cells.append(center_like(diff_text, previous_cell, next_cell))
            else:
                output_cells.append(next_cell)

        output_lines.append("|" + "|".join(output_cells) + "|")

    return output_lines


def run(args):
    lines = read_lines(args.log_path)
    previous_tables = collect_tables_by_marker(lines, args.previous_Revised_content)
    next_tables = collect_tables_by_marker(lines, args.next_Revised_content)
    common_k_shots = sorted(set(previous_tables) & set(next_tables))

    if not common_k_shots:
        raise ValueError(
            "No matching k_shots tables found for "
            f"{args.previous_Revised_content} and {args.next_Revised_content}"
        )

    output_file = os.path.basename(args.log_path)
    logger = build_logger(args.output_dir, output_file)

    for k_shots in common_k_shots:
        comparison_table = compare_tables(
            previous_tables[k_shots]["table"],
            next_tables[k_shots]["table"],
        )
        logger.info("\n" + f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(
            "\n"
            + f"previous_Revised_content={args.previous_Revised_content}, "
            + f"next_Revised_content={args.next_Revised_content}, "
            + f"k_shots={k_shots}"
        )
        logger.info("\n" + "\n".join(comparison_table))


def parse_args(parser):
    parser.add_argument(
        "--log_path",
        type=str,
        default=os.path.join("results", "Visa", "1", "Visa_10seed_1shot_test_log.txt"),
        help="path to the test log file to compare",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.join("results", "Result_comparison"),
        help="directory to save the comparison log",
    )
    return parser.parse_args()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Compare AdaptCLIP revised result tables")
    parser.add_argument("--previous_Revised_content", type=str, default="#old")
    parser.add_argument("--next_Revised_content", type=str, default="#Top-k+gated residual")
    run(parse_args(parser))
