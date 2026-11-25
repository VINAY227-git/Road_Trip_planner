import os
from collections import Counter
from datetime import datetime
from typing import Dict, Any
from models import TripManager
from storage import DATA_DIR, ensure_data_dir, export_to_csv


def format_duration(total_mins: int) -> str:
    hrs, mins = divmod(total_mins, 60)
    return f"{hrs}h {mins:02d}m"


def compute_executive_summary(manager: TripManager) -> Dict[str, Any]:
    stops = manager.stops
    active_stops = [s for s in stops if s.status != "Skipped"]

    total_km = sum(s.distance_km for s in active_stops)
    total_mins = sum(s.est_travel_mins for s in active_stops)
    avg_km = (total_km / len(active_stops)) if active_stops else 0.0
    avg_mins = (total_mins / len(active_stops)) if active_stops else 0.0
    avg_speed = (total_km / (total_mins / 60.0)) if total_mins > 0 else 0.0

    longest_leg = max(active_stops, key=lambda s: s.distance_km, default=None)
    status_counts = Counter(s.status for s in stops)
    category_km: Dict[str, float] = {}
    for s in active_stops:
        category_km[s.category] = round(category_km.get(s.category, 0.0) + s.distance_km, 2)

    all_warnings = []
    for s in stops:
        for w in s.get_warnings():
            all_warnings.append(f"Stop #{s.order} ({s.name}): {w}")

    return {
        "total_stops": len(stops),
        "active_stops": len(active_stops),
        "total_km": round(total_km, 2),
        "total_mins": total_mins,
        "total_duration_str": format_duration(total_mins),
        "avg_km": round(avg_km, 2),
        "avg_mins": round(avg_mins, 1),
        "avg_speed_kmh": round(avg_speed, 1),
        "longest_leg": longest_leg,
        "status_counts": dict(status_counts),
        "category_km": category_km,
        "warnings": all_warnings,
    }


def export_all_reports(manager: TripManager) -> Dict[str, str]:
    """Stretch Feature: Exports Markdown summary, plain-text audit log, and CSV."""
    ensure_data_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = compute_executive_summary(manager)

    md_path = os.path.join(DATA_DIR, f"trip_summary_{stamp}.md")
    txt_path = os.path.join(DATA_DIR, f"audit_log_{stamp}.txt")
    csv_path = os.path.join(DATA_DIR, f"route_export_{stamp}.csv")

    # 1. Markdown Executive Report
    md_lines = [
        "# Road Trip Stop Planner — Executive Summary",
        f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "## Key Route Metrics",
        f"- **Total Stops:** {summary['total_stops']} ({summary['active_stops']} active)",
        f"- **Total Distance:** {summary['total_km']} km",
        f"- **Estimated Driving Time:** {summary['total_duration_str']} ({summary['total_mins']} mins)",
        f"- **Average Leg Distance:** {summary['avg_km']} km",
        f"- **Projected Average Speed:** {summary['avg_speed_kmh']} km/h\n",
        "## Route Itinerary",
        "| # | Stop Name | Category | Distance (km) | Est. Time | Status | Notes |",
        "|---|---|---|---:|---|---|---|",
    ]
    for s in manager.stops:
        md_lines.append(
            f"| {s.order} | {s.name} | {s.category} | {s.distance_km:.1f} | "
            f"{format_duration(s.est_travel_mins)} | {s.status} | {s.notes or '-'} |"
        )

    if summary["warnings"]:
        md_lines.append("\n## Threshold Warnings")
        for w in summary["warnings"]:
            md_lines.append(f"- ⚠️ {w}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # 2. Plain-Text Audit Log
    txt_lines = [
        "============================================================",
        "ROAD TRIP STOP PLANNER - AUDIT & THRESHOLD LOG",
        f"TIMESTAMP: {datetime.now().isoformat()}",
        "============================================================",
        f"RECORDS AUDITED : {summary['total_stops']}",
        f"ACTIVE DISTANCE : {summary['total_km']} km",
        f"ACTIVE DURATION : {summary['total_duration_str']}",
        f"STATUS BREAKDOWN: {summary['status_counts']}",
        "------------------------------------------------------------",
        "THRESHOLD ALERTS:",
    ]
    if summary["warnings"]:
        txt_lines.extend(f"  [ALERT] {w}" for w in summary["warnings"])
    else:
        txt_lines.append("  [OK] No threshold breaches detected.")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))

    # 3. Standardized CSV Export
    export_to_csv(manager.stops, csv_path)

    return {"markdown": md_path, "audit_txt": txt_path, "csv": csv_path}
