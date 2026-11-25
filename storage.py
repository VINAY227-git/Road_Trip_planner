import csv
import json
import os
from typing import List, Tuple
from models import RoadTripStop, ALLOWED_CATEGORIES, ALLOWED_STATUSES

DATA_DIR = "data"
DEFAULT_JSON_PATH = os.path.join(DATA_DIR, "stops.json")


def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def save_to_json(stops: List[RoadTripStop], filepath: str = DEFAULT_JSON_PATH) -> None:
    ensure_data_dir()
    payload = [s.to_dict() for s in stops]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_from_json(filepath: str = DEFAULT_JSON_PATH) -> Tuple[List[RoadTripStop], str | None]:
    """
    Fault-tolerant JSON loader. Automatically creates a clean file if missing
    or backs up corrupted files instead of crashing.
    """
    ensure_data_dir()
    if not os.path.exists(filepath):
        save_to_json([], filepath)
        return [], "Initialized fresh local storage file."

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        if not isinstance(raw_data, list):
            raise ValueError("Root JSON element must be a list.")
        stops = [RoadTripStop.from_dict(item) for item in raw_data]
        return stops, None
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        backup_path = f"{filepath}.corrupted.bak"
        os.replace(filepath, backup_path)
        save_to_json([], filepath)
        return [], f"Corrupted JSON backed up to {backup_path} ({exc}). Started clean store."


def export_to_csv(stops: List[RoadTripStop], filepath: str) -> None:
    ensure_data_dir()
    fieldnames = [
        "stop_id", "order", "name", "category",
        "distance_km", "est_travel_mins", "status", "notes", "created_at"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in stops:
            writer.writerow(s.to_dict())


def bulk_import_csv(filepath: str, starting_id: int, starting_order: int) -> Tuple[List[RoadTripStop], List[str]]:
    """
    Stretch Feature: Ingests legacy CSV files with row-by-row schema & range validation.
    Returns (valid_stops, error_logs).
    """
    valid_stops: List[RoadTripStop] = []
    error_logs: List[str] = []

    if not os.path.exists(filepath):
        return [], [f"File not found: {filepath}"]

    next_id = starting_id
    next_order = starting_order

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required_cols = {"name", "category", "distance_km", "est_travel_mins"}
        if not reader.fieldnames or not required_cols.issubset({c.strip() for c in reader.fieldnames}):
            return [], [f"Missing required columns. Expected at least: {', '.join(sorted(required_cols))}"]

        for row_num, row in enumerate(reader, start=2):
            try:
                name = (row.get("name") or "").strip()
                if len(name) < 2:
                    raise ValueError("Stop name must be at least 2 characters.")

                category = (row.get("category") or "").strip().title()
                if category not in ALLOWED_CATEGORIES:
                    raise ValueError(f"Invalid category '{category}'. Allowed: {ALLOWED_CATEGORIES}")

                dist = float(row.get("distance_km", -1))
                if not (0 <= dist <= 5000):
                    raise ValueError(f"Distance {dist} km out of valid range (0–5000).")

                mins = int(float(row.get("est_travel_mins", -1)))
                if not (0 <= mins <= 2880):
                    raise ValueError(f"Travel time {mins} mins out of valid range (0–2880).")

                status = (row.get("status") or "Planned").strip().title()
                if status not in ALLOWED_STATUSES:
                    raise ValueError(f"Invalid status '{status}'. Allowed: {ALLOWED_STATUSES}")

                notes = (row.get("notes") or "").strip()

                stop = RoadTripStop(
                    stop_id=next_id,
                    order=next_order,
                    name=name,
                    category=category,
                    distance_km=round(dist, 2),
                    est_travel_mins=mins,
                    status=status,
                    notes=notes,
                    created_at=(row.get("created_at") or "").strip() or "Imported",
                )
                valid_stops.append(stop)
                next_id += 1
                next_order += 1
            except Exception as e:
                error_logs.append(f"Row {row_num}: {e}")

    return valid_stops, error_logs
