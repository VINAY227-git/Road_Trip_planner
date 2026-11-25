import os
import re
from models import TripManager, ALLOWED_CATEGORIES, ALLOWED_STATUSES
from storage import load_from_json, save_to_json, bulk_import_csv, DEFAULT_JSON_PATH
from reports import compute_executive_summary, export_all_reports, format_duration

# ANSI Escape Codes for clean terminal styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def prompt_text(label: str, min_len: int = 2, max_len: int = 60, allow_blank: bool = False) -> str:
    """Centralized defensive text input wrapper."""
    pattern = re.compile(r"^[A-Za-z0-9\s\-\.,'()&/]+$")
    while True:
        val = input(f"{CYAN}{label}{RESET}").strip()
        if not val and allow_blank:
            return ""
        if len(val) < min_len or len(val) > max_len:
            print(f"{RED}✖ Input must be between {min_len} and {max_len} characters.{RESET}")
            continue
        if not pattern.match(val):
            print(f"{RED}✖ Contains unsupported characters. Use letters, numbers, or basic punctuation.{RESET}")
            continue
        return val


def prompt_float(label: str, min_val: float = 0.0, max_val: float = 5000.0) -> float:
    """Centralized defensive float input wrapper."""
    while True:
        raw = input(f"{CYAN}{label}{RESET}").strip()
        try:
            val = float(raw)
            if not (min_val <= val <= max_val):
                print(f"{RED}✖ Value must be between {min_val} and {max_val}.{RESET}")
                continue
            return round(val, 2)
        except ValueError:
            print(f"{RED}✖ Invalid number '{raw}'. Enter a valid numeric value.{RESET}")


def prompt_int(label: str, min_val: int = 1, max_val: int = 9999, allow_blank: bool = False) -> int | None:
    """Centralized defensive integer input wrapper."""
    while True:
        raw = input(f"{CYAN}{label}{RESET}").strip()
        if not raw and allow_blank:
            return None
        try:
            val = int(raw)
            if not (min_val <= val <= max_val):
                print(f"{RED}✖ Enter a whole number between {min_val} and {max_val}.{RESET}")
                continue
            return val
        except ValueError:
            print(f"{RED}✖ Invalid integer '{raw}'. Please try again.{RESET}")


def prompt_choice(label: str, options: tuple[str, ...]) -> str:
    """Validates categorical selection case-insensitively."""
    formatted_opts = "/".join(options)
    while True:
        raw = input(f"{CYAN}{label} [{formatted_opts}]: {RESET}").strip()
        for opt in options:
            if raw.lower() == opt.lower():
                return opt
        print(f"{RED}✖ Invalid choice '{raw}'. Choose from: {formatted_opts}{RESET}")


def render_stops_table(schedule_rows: list, page_size: int = 15) -> None:
    """Renders paginated fixed-width terminal tables with warning badges."""
    if not schedule_rows:
        print(f"{YELLOW}No road trip stops found.{RESET}")
        return

    total = len(schedule_rows)
    for start in range(0, total, page_size):
        chunk = schedule_rows[start : start + page_size]
        print(f"\n{BOLD}{'-'*106}")
        print(f"{'#':<4} {'ID':<4} {'Stop Name':<24} {'Category':<12} {'Leg km':>8} {'Cum. km':>9} {'Time':>8} {'Status':<10} {'Flags'}")
        print(f"{'-'*106}{RESET}")

        for item in chunk:
            s = item["stop"]
            warns = item["warnings"]
            flag_str = f"{YELLOW}⚠ {warns[0]}{RESET}" if warns else f"{GREEN}OK{RESET}"
            status_color = GREEN if s.status == "Completed" else (DIM if s.status == "Skipped" else CYAN)

            print(
                f"{s.order:<4} {s.stop_id:<4} {s.name[:23]:<24} {s.category:<12} "
                f"{s.distance_km:>8.1f} {item['cum_km']:>9.1f} {format_duration(s.est_travel_mins):>8} "
                f"{status_color}{s.status:<10}{RESET} {flag_str}"
            )
            if s.notes:
                print(f"     {DIM}└─ Note: {s.notes[:85]}{RESET}")

        print(f"{'-'*106}")
        if start + page_size < total:
            cont = input(f"{DIM}Showing {start + len(chunk)}/{total}. Press Enter for next page or 'q' to stop: {RESET}")
            if cont.strip().lower() == "q":
                break


def handle_add_stop(manager: TripManager) -> None:
    print(f"\n{BOLD}--- Add New Road Trip Stop ---{RESET}")
    name = prompt_text("Stop / Landmark Name: ", min_len=2, max_len=50)
    category = prompt_choice("Category", ALLOWED_CATEGORIES)
    distance_km = prompt_float("Estimated Leg Distance (km, 0–5000): ", 0.0, 5000.0)
    est_mins = prompt_int("Estimated Travel Time (minutes, 0–2880): ", 0, 2880)
    status = prompt_choice("Status", ALLOWED_STATUSES)
    notes = prompt_text("Travel-Time / Route Notes (optional): ", min_len=0, max_len=120, allow_blank=True)
    pos = prompt_int(
        f"Insert at Route Position (1–{len(manager.stops)+1}, Enter for end): ",
        1,
        len(manager.stops) + 1,
        allow_blank=True,
    )

    stop = manager.add_stop(name, category, distance_km, est_mins, status, notes, pos)
    save_to_json(manager.stops)
    print(f"{GREEN}✔ Added Stop #{stop.order}: '{stop.name}' (ID: {stop.stop_id}).{RESET}")
    for w in stop.get_warnings():
        print(f"{YELLOW}⚠ Threshold Warning: {w}{RESET}")


def handle_search(manager: TripManager) -> None:
    print(f"\n{BOLD}--- Search & Filter Stops ---{RESET}")
    kw = input(f"{CYAN}Keyword (name/notes, Enter to skip): {RESET}").strip()
    cat = input(f"{CYAN}Category filter {ALLOWED_CATEGORIES} (Enter to skip): {RESET}").strip()
    stat = input(f"{CYAN}Status filter {ALLOWED_STATUSES} (Enter to skip): {RESET}").strip()

    matches = manager.search(keyword=kw, category=cat, status=stat)
    wrapped = [{"stop": s, "cum_km": s.distance_km, "warnings": s.get_warnings()} for s in matches]
    print(f"\n{GREEN}Found {len(matches)} matching record(s):{RESET}")
    render_stops_table(wrapped)


def handle_summary(manager: TripManager) -> None:
    summary = compute_executive_summary(manager)
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗")
    print(f"║           EXECUTIVE ROAD TRIP SUMMARY REPORT             ║")
    print(f"╚══════════════════════════════════════════════════════════╝{RESET}")
    print(f"  Total Planned Stops   : {BOLD}{summary['total_stops']}{RESET} (Active: {summary['active_stops']})")
    print(f"  Total Route Distance  : {BOLD}{summary['total_km']} km{RESET}")
    print(f"  Total Driving Time    : {BOLD}{summary['total_duration_str']}{RESET} ({summary['total_mins']} mins)")
    print(f"  Average Leg Distance  : {BOLD}{summary['avg_km']} km{RESET}")
    print(f"  Average Leg Time      : {BOLD}{summary['avg_mins']} mins{RESET}")
    print(f"  Projected Avg Speed   : {BOLD}{summary['avg_speed_kmh']} km/h{RESET}")

    if summary["longest_leg"]:
        ll = summary["longest_leg"]
        print(f"  Longest Single Leg    : {BOLD}{ll.name} ({ll.distance_km} km){RESET}")

    print(f"\n{BOLD}  Status Breakdown:{RESET}")
    for st, count in summary["status_counts"].items():
        print(f"    • {st:<12}: {count}")

    print(f"\n{BOLD}  Distance by Category:{RESET}")
    for cat, km in summary["category_km"].items():
        print(f"    • {cat:<12}: {km:.1f} km")

    if summary["warnings"]:
        print(f"\n{YELLOW}{BOLD}  Threshold Warning Indicators ({len(summary['warnings'])}):{RESET}")
        for w in summary["warnings"]:
            print(f"    {YELLOW}⚠ {w}{RESET}")
    else:
        print(f"\n{GREEN}  ✔ All route legs fall within safe distance and fatigue thresholds.{RESET}")


def handle_bulk_import(manager: TripManager) -> None:
    print(f"\n{BOLD}--- Bulk CSV Dataset Import ---{RESET}")
    path = input(f"{CYAN}Enter path to CSV file (e.g., sample_import.csv): {RESET}").strip()
    imported, errors = bulk_import_csv(path, manager.next_id(), len(manager.stops) + 1)
    if imported:
        manager.stops.extend(imported)
        manager._normalize_orders()
        save_to_json(manager.stops)
        print(f"{GREEN}✔ Successfully imported {len(imported)} stop(s).{RESET}")
    if errors:
        print(f"{YELLOW}⚠ Row-by-Row Validation Log ({len(errors)} skipped):{RESET}")
        for err in errors:
            print(f"  {RED}• {err}{RESET}")


def main() -> None:
    stops, init_msg = load_from_json(DEFAULT_JSON_PATH)
    manager = TripManager(stops)

    print(f"{BOLD}{CYAN}============================================================")
    print("   ROAD TRIP STOP PLANNER  |  LocalImpact Challenge #60")
    print(f"============================================================{RESET}")
    if init_msg:
        print(f"{YELLOW}[Storage Notice] {init_msg}{RESET}")
    print(f"{GREEN}Loaded {len(manager.stops)} stop(s) from {DEFAULT_JSON_PATH}.{RESET}")

    while True:
        print(f"\n{BOLD}MAIN MENU:{RESET}")
        print("  1. View Full Itinerary & Cumulative Distances")
        print("  2. Add New Road Trip Stop")
        print("  3. Reorder a Stop in Route")
        print("  4. Update Stop Status (Planned / Completed / Skipped)")
        print("  5. Search & Filter Stops")
        print("  6. Executive Summary & Threshold Warnings")
        print("  7. Export Reports (Markdown, Audit Log, CSV)")
        print("  8. Bulk Import Stops from CSV")
        print("  9. Delete a Stop")
        print("  0. Exit")

        choice = input(f"\n{CYAN}Select an option [0–9]: {RESET}").strip()

        if choice == "1":
            render_stops_table(manager.get_cumulative_schedule())
        elif choice == "2":
            handle_add_stop(manager)
        elif choice == "3":
            if not manager.stops:
                print(f"{YELLOW}No stops available to reorder.{RESET}")
                continue
            render_stops_table(manager.get_cumulative_schedule())
            sid = prompt_int("Enter Stop ID to move: ", 1, 99999)
            pos = prompt_int(f"Enter new route position (1–{len(manager.stops)}): ", 1, len(manager.stops))
            if manager.reorder_stop(sid, pos):
                save_to_json(manager.stops)
                print(f"{GREEN}✔ Route order updated and saved.{RESET}")
            else:
                print(f"{RED}✖ Stop ID {sid} not found.{RESET}")
        elif choice == "4":
            sid = prompt_int("Enter Stop ID to update: ", 1, 99999)
            new_st = prompt_choice("New Status", ALLOWED_STATUSES)
            if manager.update_status(sid, new_st):
                save_to_json(manager.stops)
                print(f"{GREEN}✔ Updated Stop ID {sid} to '{new_st}'.{RESET}")
            else:
                print(f"{RED}✖ Stop ID {sid} not found.{RESET}")
        elif choice == "5":
            handle_search(manager)
        elif choice == "6":
            handle_summary(manager)
        elif choice == "7":
            paths = export_all_reports(manager)
            print(f"{GREEN}✔ Reports exported successfully:{RESET}")
            for fmt, p in paths.items():
                print(f"  • {fmt.upper():<10}: {p}")
        elif choice == "8":
            handle_bulk_import(manager)
        elif choice == "9":
            sid = prompt_int("Enter Stop ID to delete: ", 1, 99999)
            if manager.delete_stop(sid):
                save_to_json(manager.stops)
                print(f"{GREEN}✔ Deleted Stop ID {sid}.{RESET}")
            else:
                print(f"{RED}✖ Stop ID {sid} not found.{RESET}")
        elif choice == "0":
            save_to_json(manager.stops)
            print(f"{CYAN}State saved to {DEFAULT_JSON_PATH}. Safe travels!{RESET}")
            break
        else:
            print(f"{RED}✖ Invalid menu option. Choose 0–9.{RESET}")


if __name__ == "__main__":
    main()
