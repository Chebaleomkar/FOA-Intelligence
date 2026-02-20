"""
JSON & CSV Exporters — Write FOA records to structured output files.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List

from src.extraction.schema import FOARecord

logger = logging.getLogger(__name__)


def export_json(records: List[FOARecord], output_path: Path) -> Path:
    """
    Export FOA records to a JSON file.

    Args:
        records: List of FOARecord objects to export.
        output_path: Path to write the JSON file.

    Returns:
        Path to the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [record.model_dump(mode="json") for record in records]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    logger.info(f"Exported {len(records)} FOA records to {output_path}")
    return output_path


def export_csv(records: List[FOARecord], output_path: Path) -> Path:
    """
    Export FOA records to a CSV file.

    Semantic tags are flattened into a semicolon-separated string.

    Args:
        records: List of FOARecord objects to export.
        output_path: Path to write the CSV file.

    Returns:
        Path to the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        logger.warning("No records to export to CSV")
        return output_path

    # Get flat dictionaries
    flat_records = [record.to_flat_dict() for record in records]

    # Determine CSV columns from the first record
    fieldnames = list(flat_records[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_records)

    logger.info(f"Exported {len(records)} FOA records to {output_path}")
    return output_path
