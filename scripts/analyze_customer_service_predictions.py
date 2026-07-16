#!/usr/bin/env python3
"""Compute deterministic integrity metrics for generated customer-service answers."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


IDENTIFIER_PATTERN = re.compile(r"TEST-[A-Za-z0-9-]+")


def normalize(text: str) -> str:
    return "".join(text.split()).replace("<|im_end|>", "")


def identifiers(text: str) -> set[str]:
    return set(IDENTIFIER_PATTERN.findall(text))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = [
        json.loads(line)
        for line in args.predictions.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("prediction file is empty")

    exact_indices = [
        index
        for index, row in enumerate(rows)
        if normalize(row["predict"]) == normalize(row["label"])
    ]
    grounded_indices = [
        index
        for index, row in enumerate(rows)
        if identifiers(row["predict"]).issubset(identifiers(row["prompt"]))
    ]
    identifier_match_indices = [
        index
        for index, row in enumerate(rows)
        if identifiers(row["predict"]) == identifiers(row["label"])
    ]
    lengths = [len(row["predict"]) for row in rows]

    result = {
        "count": len(rows),
        "normalized_exact_match": len(exact_indices) / len(rows),
        "normalized_exact_match_count": len(exact_indices),
        "empty_prediction_count": sum(not row["predict"].strip() for row in rows),
        "special_token_leak_count": sum("<|" in row["predict"] for row in rows),
        "identifier_grounding_rate": len(grounded_indices) / len(rows),
        "identifier_grounding_count": len(grounded_indices),
        "identifier_reference_match_rate": len(identifier_match_indices) / len(rows),
        "identifier_reference_match_count": len(identifier_match_indices),
        "prediction_chars_min": min(lengths),
        "prediction_chars_mean": statistics.mean(lengths),
        "prediction_chars_max": max(lengths),
        "non_exact_indices": sorted(set(range(len(rows))) - set(exact_indices)),
        "ungrounded_identifier_indices": sorted(set(range(len(rows))) - set(grounded_indices)),
    }
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(output, end="")
    if args.output:
        args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
