# Road Trip Stop Planner (LocalImpact Challenge #60)

A zero-dependency Python 3.10+ terminal application engineered to arrange road trip stops, compute cumulative distances and travel times, enforce strict input validation, persist records in JSON/CSV, and generate executive summaries.

## Project Structure
- `main.py` — Interactive ANSI terminal interface, input wrappers, and menu loop
- `models.py` — `RoadTripStop` dataclass, `TripManager` business logic, and threshold warning checks
- `storage.py` — Fault-tolerant JSON persistence, CSV export, and bulk CSV import with row-by-row error logs
- `reports.py` — Executive summary metrics and multi-format report exports (Markdown, plain-text audit log, CSV)
- `seed_data.py` — Populates `data/stops.json` with 35 realistic sample entries and generates `sample_import.csv`

## Quick Start
1. Open the folder in VS Code and launch the integrated terminal.
2. Seed the 35-stop sample dataset (also pre-included in `data/`):
   ```bash
   python seed_data.py
   ```
3. Run the application:
   ```bash
   python main.py
   ```
