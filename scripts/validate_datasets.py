#!/usr/bin/env python3
"""Validate customer-service dataset schema, split isolation, and hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
FILES = {
    "train": ("customer_service_train.json", 500),
    "validation": ("customer_service_validation.json", 100),
    "smoke": ("customer_service_smoke.json", 50),
}
REQUIRED_FIELDS = {"system", "instruction", "input", "output"}


def fingerprint(record: dict[str, object]) -> str:
    normalized = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_record(record: object, split: str, index: int) -> dict[str, object]:
    if not isinstance(record, dict):
        raise ValueError(f"{split}[{index}] must be an object")
    missing = REQUIRED_FIELDS - record.keys()
    if missing:
        raise ValueError(f"{split}[{index}] missing fields: {sorted(missing)}")
    for field in REQUIRED_FIELDS:
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"{split}[{index}].{field} must be a non-empty string")
    if "history" in record:
        history = record["history"]
        if not isinstance(history, list):
            raise ValueError(f"{split}[{index}].history must be a list")
        for turn in history:
            if (
                not isinstance(turn, list)
                or len(turn) != 2
                or not all(isinstance(message, str) and message.strip() for message in turn)
            ):
                raise ValueError(f"{split}[{index}] has an invalid history turn")
    return record


def main() -> None:
    split_fingerprints: dict[str, set[str]] = {}
    dataset_info = json.loads((DATASET_DIR / "dataset_info.json").read_text(encoding="utf-8"))

    for split, (filename, expected_count) in FILES.items():
        dataset_name = f"customer_service_{split}"
        if dataset_name not in dataset_info:
            raise ValueError(f"dataset_info.json is missing {dataset_name}")
        if dataset_info[dataset_name].get("file_name") != filename:
            raise ValueError(f"dataset_info.json has an invalid file for {dataset_name}")
        path = DATASET_DIR / filename
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError(f"{filename} must contain a JSON array")
        if len(records) != expected_count:
            raise ValueError(f"{filename}: expected {expected_count}, got {len(records)}")

        fingerprints = {
            fingerprint(validate_record(record, split, index))
            for index, record in enumerate(records)
        }
        if len(fingerprints) != len(records):
            raise ValueError(f"{filename} contains exact duplicate records")
        split_fingerprints[split] = fingerprints

        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{split:10} count={len(records):3d} sha256={sha256}")

    split_names = list(split_fingerprints)
    for index, left in enumerate(split_names):
        for right in split_names[index + 1 :]:
            overlap = split_fingerprints[left] & split_fingerprints[right]
            if overlap:
                raise ValueError(f"data leakage: {left} and {right} overlap by {len(overlap)} records")

    print("schema=ok duplicates=0 cross_split_overlap=0")


if __name__ == "__main__":
    main()
