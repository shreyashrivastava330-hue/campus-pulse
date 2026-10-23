"""
CampusPulse — Data Mining and Data Warehousing Project
Synthetic Dataset Generator

Generates 400 realistic campus issue reports for demonstration.
"""

import csv
import random
from datetime import datetime, timedelta

# Category definitions
CATEGORIES = ["Wi-Fi", "Water", "Cleanliness", "Canteen", "Equipment"]

LOCATIONS = [
    "Library Block A", "Library Block B",
    "Academic Block A", "Academic Block B", "Academic Block C",
    "Hostel Block 1", "Hostel Block 2",
    "Canteen Area", "Lab Building",
    "Sports Complex", "Main Gate Area"
]

STATUSES = ["Pending", "In Progress", "Resolved"]

# Realistic issue descriptions by category
DESCRIPTIONS = {
    "Wi-Fi": [
        "Wi-Fi keeps disconnecting in the study area",
        "Internet very slow in this building",
        "Cannot connect to network at all",
        "Wi-Fi signal is very weak here",
        "Network connectivity issues affecting classes",
        "Intermittent connectivity problems",
        "Router needs to be rebooted",
    ],
    "Water": [
        "Water dispenser is not working",
        "Leaking pipe near the washroom",
        "No water available in Block B",
        "Water quality is poor",
        "Broken water tap in the lab",
        "Water overflow in the corridor",
    ],
    "Cleanliness": [
        "Washroom is very dirty",
        "Dust accumulation in classroom",
        "Trash not being collected regularly",
        "Floor is not cleaned properly",
        "Sweeping and mopping not done",
        "Dustbins overflowing",
    ],
    "Canteen": [
        "Long queues during lunch hours",
        "Quality of food has deteriorated",
        "Prices are too high",
        "Canteen is always crowded",
        "Menu items often unavailable",
        "Seating capacity is insufficient",
    ],
    "Equipment": [
        "Projector is not working in Lecture Hall 3",
        "Classroom whiteboard marker supply depleted",
        "AC is broken in the auditorium",
        "Computer lab systems are down",
        "Microphone system in conference room is faulty",
        "Door lock is broken",
    ],
}


def generate_dataset(num_records=400, output_file="campus_issues.csv"):
    """Generate synthetic campus issue dataset."""
    records = []
    base_date = datetime(2026, 8, 1)

    for i in range(num_records):
        report_id = 1000 + i
        category = random.choice(CATEGORIES)
        description = random.choice(DESCRIPTIONS[category])
        location = random.choice(LOCATIONS)
        status = random.choices(STATUSES, weights=[0.3, 0.2, 0.5])[0]

        # Generate realistic timestamps
        days_offset = random.randint(0, 70)
        reported_at = base_date + timedelta(days=days_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        # Resolution time (if resolved)
        resolved_at = None
        if status == "Resolved":
            resolution_hours = random.randint(1, 168)
            resolved_at = reported_at + timedelta(hours=resolution_hours)

        records.append({
            "report_id": report_id,
            "description": description,
            "category": category,
            "location": location,
            "reported_at": reported_at.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else "",
        })

    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["report_id", "description", "category", "location", "reported_at", "status", "resolved_at"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {num_records} synthetic records in {output_file}")
    print(f"Category distribution: {dict((c, sum(1 for r in records if r['category'] == c)) for c in CATEGORIES)}")
    return output_file


if __name__ == "__main__":
    generate_dataset(400, "data/campus_issues.csv")
