"""
CampusPulse — ETL Pipeline and Data Warehouse Module

Extracts, transforms, and loads data into SQLite star schema.
"""

import sqlite3
import pandas as pd
import re
from datetime import datetime
import threading


class CampusIssueWarehouse:
    """SQLite-based star-schema data warehouse for campus issues."""

    def __init__(self, db_path="data/campus_issues.db"):
        self.db_path = db_path
        # Enable check_same_thread=False to allow Streamlit's multi-threaded access
        # Protected by threading lock for safety
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._lock = threading.Lock()
        self.create_schema()

    def create_schema(self):
        """Create star-schema tables."""
        # Dimension: Date
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DimDate (
                date_key INTEGER PRIMARY KEY,
                full_date TEXT UNIQUE,
                day INTEGER,
                month INTEGER,
                quarter INTEGER,
                year INTEGER,
                day_of_week TEXT,
                is_weekend INTEGER
            )
        """)

        # Dimension: Location
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DimLocation (
                location_key INTEGER PRIMARY KEY AUTOINCREMENT,
                building_name TEXT UNIQUE,
                floor TEXT,
                area_type TEXT
            )
        """)

        # Dimension: Category
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DimCategory (
                category_key INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE,
                category_group TEXT
            )
        """)

        # Dimension: Status
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DimStatus (
                status_key INTEGER PRIMARY KEY AUTOINCREMENT,
                status_label TEXT UNIQUE
            )
        """)

        # Fact Table: Campus Issues
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS FactCampusIssues (
                fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER UNIQUE,
                date_key INTEGER,
                location_key INTEGER,
                category_key INTEGER,
                status_key INTEGER,
                description TEXT,
                resolution_hours REAL,
                FOREIGN KEY (date_key) REFERENCES DimDate(date_key),
                FOREIGN KEY (location_key) REFERENCES DimLocation(location_key),
                FOREIGN KEY (category_key) REFERENCES DimCategory(category_key),
                FOREIGN KEY (status_key) REFERENCES DimStatus(status_key)
            )
        """)

        self.conn.commit()

    def load_dimensions(self):
        """Pre-load dimension tables with known values."""
        # Status dimension
        statuses = ["Pending", "In Progress", "Resolved"]
        for s in statuses:
            self.cursor.execute(
                "INSERT OR IGNORE INTO DimStatus (status_label) VALUES (?)",
                (s,)
            )

        # Category dimension
        categories = [
            ("Wi-Fi", "Infrastructure"),
            ("Water", "Infrastructure"),
            ("Equipment", "Infrastructure"),
            ("Cleanliness", "Services"),
            ("Canteen", "Services"),
        ]
        for cat, group in categories:
            self.cursor.execute(
                "INSERT OR IGNORE INTO DimCategory (category_name, category_group) VALUES (?, ?)",
                (cat, group)
            )

        self.conn.commit()

    def get_or_create_date_key(self, date_str):
        """Get or create a date key for a timestamp string."""
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        day_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]
        is_weekend = 1 if dt.weekday() >= 5 else 0
        quarter = (dt.month - 1) // 3 + 1

        date_key = int(dt.strftime("%Y%m%d"))
        self.cursor.execute("""
            INSERT OR IGNORE INTO DimDate
            (date_key, full_date, day, month, quarter, year, day_of_week, is_weekend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_key, dt.strftime("%Y-%m-%d"), dt.day, dt.month, quarter, dt.year, day_of_week, is_weekend))

        return date_key

    def get_key(self, table, column, value):
        """Get the primary key for a dimension value."""
        self.cursor.execute(f"SELECT {table[3:].lower()}_key FROM {table} WHERE {column} = ?", (value,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def load_data(self, csv_path):
        """Load and transform data from CSV into the warehouse."""
        df = pd.read_csv(csv_path)
        print(f"Loading {len(df)} records from {csv_path}")

        # Data preprocessing
        df = self._preprocess(df)

        # Load dimension records
        self.load_dimensions()
        for loc in df["location"].unique():
            self.cursor.execute(
                "INSERT OR IGNORE INTO DimLocation (building_name, area_type) VALUES (?, ?)",
                (loc, "Campus Area")
            )
        self.conn.commit()

        # Load fact records
        for _, row in df.iterrows():
            date_key = self.get_or_create_date_key(row["reported_at"])
            location_key = self.get_key("DimLocation", "building_name", row["location"])
            category_key = self.get_key("DimCategory", "category_name", row["category"])
            status_key = self.get_key("DimStatus", "status_label", row["status"])

            resolution_hours = None
            if row["status"] == "Resolved" and pd.notna(row["resolved_at"]):
                reported = datetime.strptime(row["reported_at"], "%Y-%m-%d %H:%M:%S")
                resolved = datetime.strptime(row["resolved_at"], "%Y-%m-%d %H:%M:%S")
                resolution_hours = (resolved - reported).total_seconds() / 3600

            self.cursor.execute("""
                INSERT INTO FactCampusIssues
                (report_id, date_key, location_key, category_key, status_key, description, resolution_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (int(row["report_id"]), date_key, location_key, category_key, status_key, row["description"], resolution_hours))

        self.conn.commit()
        print(f"Loaded {len(df)} records into warehouse")

    def _preprocess(self, df):
        """Preprocess data: clean, standardize, handle missing values."""
        # Remove duplicates
        df = df.drop_duplicates(subset=["description", "reported_at"], keep="first")

        # Handle missing values
        df = df.dropna(subset=["description", "category", "location", "reported_at"])

        # Standardize category names
        category_map = {
            "wifi": "Wi-Fi", "wi-fi": "Wi-Fi", "internet": "Wi-Fi",
            "water": "Water", "cleanliness": "Cleanliness", "clean": "Cleanliness",
            "canteen": "Canteen", "food": "Canteen",
            "equipment": "Equipment", "lab": "Equipment",
        }
        df["category"] = df["category"].str.strip().apply(
            lambda x: category_map.get(x.lower(), x)
        )

        # Text normalization
        df["description"] = df["description"].str.lower().str.strip()
        df["description"] = df["description"].apply(lambda x: re.sub(r'[^a-z0-9\s]', '', x))

        # Location standardization
        df["location"] = df["location"].str.strip()

        return df

    def query(self, sql):
        """Execute a SQL query and return results as DataFrame."""
        with self._lock:
            return pd.read_sql_query(sql, self.conn)

    def close(self):
        """Close the database connection."""
        with self._lock:
            if self.conn:
                self.conn.close()


if __name__ == "__main__":
    wh = CampusIssueWarehouse("data/campus_issues.db")
    wh.load_data("data/campus_issues.csv")

    # Test query
    result = wh.query("""
        SELECT c.category_name, COUNT(*) as issue_count
        FROM FactCampusIssues f
        JOIN DimCategory c ON f.category_key = c.category_key
        GROUP BY c.category_name
        ORDER BY issue_count DESC
    """)
    print("\nIssues by Category:")
    print(result)

    wh.close()
