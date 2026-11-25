import csv
from models import TripManager
from storage import save_to_json, DEFAULT_JSON_PATH


def generate_demo_data() -> None:
    manager = TripManager()

    sample_entries = [
        ("Hyderabad ORR Exit 1", "Toll", 18.5, 22, "Completed", "FASTag active; smooth morning exit"),
        ("Jadcherla Highway Plaza", "Food", 78.0, 65, "Completed", "Breakfast stop; clean restrooms"),
        ("Kurnool Tungabhadra Bridge", "Scenic", 132.4, 115, "Completed", "Quick river viewpoint photo stop"),
        ("Gooty Fort Overlook", "Sightseeing", 96.0, 90, "Completed", "Hilltop view; 20-min detour"),
        ("Anantapur HPCL Fuel Hub", "Fuel", 54.2, 48, "Completed", "Full tank refill + tire pressure check"),
        ("Penukonda Heritage Rest", "Rest", 71.0, 65, "Completed", "15-minute driver stretch"),
        ("Chikkaballapur Nandi Turn", "Scenic", 112.5, 105, "Completed", "Foggy morning stretch near hills"),
        ("Devanahalli Airport Toll", "Toll", 34.0, 35, "Completed", "Moderate weekday traffic"),
        ("Bengaluru Hebbal Junction", "Rest", 26.8, 55, "Completed", "Heavy peak-hour bottleneck"),
        ("Bidadi Thatte Idli Point", "Food", 42.0, 50, "Planned", "Lunch break before Mysore Expressway"),
        ("Mandya Sugarcane Belt", "Fuel", 64.5, 52, "Planned", "Top-up fuel before ghat climb"),
        ("Srirangapatna Island Fort", "Sightseeing", 28.0, 30, "Planned", "Historic stop along Kaveri river"),
        ("Mysuru Ring Road Stay", "Lodging", 19.2, 25, "Planned", "Overnight halt; EV/covered parking"),
        ("Nanjangud Temple Bypass", "Toll", 27.5, 30, "Planned", "Early 6 AM departure"),
        ("Bandipur Tiger Reserve Gate", "Scenic", 54.0, 65, "Planned", "Strict 40 km/h forest speed limit"),
        ("Mudumalai Teak Forest", "Rest", 22.0, 40, "Planned", "No-stopping zone except checkpost"),
        ("Gudalur Valley Viewpoint", "Scenic", 31.4, 50, "Planned", "Tea estate photography break"),
        ("Kalpetta Wayanad Cafe", "Food", 58.0, 85, "Planned", "Hairpin bends; allow extra buffer"),
        ("Vythiri Rainforest Lodge", "Lodging", 14.5, 25, "Planned", "Second night stay in hills"),
        ("Thamarassery Churam Hairpins", "Scenic", 18.0, 45, "Planned", "9 hairpin bends; slow downhill gear"),
        ("Kozhikode Beach Promenade", "Sightseeing", 46.2, 65, "Planned", "Sunset coastal walk"),
        ("Thrissur Bypass Fuel Stop", "Fuel", 118.0, 130, "Planned", "NH-66 road widening diversions"),
        ("Edappally Kochi Junction", "Rest", 74.5, 95, "Planned", "Heavy metro corridor congestion"),
        ("Alappuzha Backwater Jetty", "Sightseeing", 58.0, 70, "Planned", "Houseboat boarding point"),
        ("Kollam Ashtamudi Bridge", "Scenic", 86.0, 95, "Planned", "Coastal highway stretch"),
        ("Varkala Cliff Stay", "Lodging", 41.0, 55, "Planned", "Overnight beach cliff stay"),
        ("Thiruvananthapuram Bypass", "Toll", 44.5, 50, "Planned", "Smooth 4-lane bypass"),
        ("Kanyakumari Sunrise Point", "Sightseeing", 91.0, 110, "Planned", "Southernmost tip milestone"),
        ("Tirunelveli Halwa & Fuel", "Fuel", 84.0, 80, "Planned", "NH-44 straight highway return leg"),
        ("Madurai Meenakshi Bypass", "Food", 158.0, 145, "Planned", "Lunch halt near ring road"),
        ("Salem Steel City Junction", "Rest", 236.0, 210, "Planned", "Driver rotation and tea break"),
        ("Dharmapuri Ghat Toll", "Toll", 68.0, 60, "Planned", "Smooth six-lane highway"),
        ("Krishnagiri Mega Marathon Leg", "Fuel", 445.0, 360, "Planned", "Boundary test: triggers >400km & >5.5h warnings"),
        ("Vellore Golden Temple Detour", "Sightseeing", 115.0, 105, "Skipped", "Skipped due to tight return schedule"),
        ("Chennai Marina Finish Line", "Sightseeing", 138.0, 140, "Planned", "Final trip destination"),
    ]

    for entry in sample_entries:
        manager.add_stop(*entry)

    save_to_json(manager.stops, DEFAULT_JSON_PATH)
    print(f"Seeded {len(manager.stops)} stops into {DEFAULT_JSON_PATH}")

    # Also generate a test CSV with intentional errors to demo Bulk Import validation
    with open("sample_import.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "category", "distance_km", "est_travel_mins", "status", "notes"])
        writer.writerow(["Lonavala Ghat Cafe", "Food", "65.5", "70", "Planned", "Valid imported stop"])
        writer.writerow(["Pune Expressway Toll", "Toll", "42.0", "35", "Planned", "Valid imported toll"])
        writer.writerow(["X", "Food", "20", "20", "Planned", "Invalid: name too short"])
        writer.writerow(["Bad Category Stop", "Spaceship", "50", "45", "Planned", "Invalid category"])
        writer.writerow(["Negative Distance", "Fuel", "-15", "30", "Planned", "Invalid range"])

    print("Created sample_import.csv (2 valid rows, 3 invalid rows) for bulk import testing.")


if __name__ == "__main__":
    generate_demo_data()
