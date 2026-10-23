"""
Test suite for warehouse.py - ETL pipeline and star schema.
"""

import pytest
import sqlite3
import pandas as pd


def test_warehouse_schema_creation(empty_warehouse):
    """Test that all required tables are created."""
    wh = empty_warehouse

    # Get all table names
    cursor = wh.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = {row[0] for row in cursor.fetchall()}

    # Verify all required tables exist
    required_tables = {"DimDate", "DimLocation", "DimCategory", "DimStatus", "FactCampusIssues"}
    assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"


def test_dimension_loading(empty_warehouse):
    """Test that dimension tables are correctly pre-loaded."""
    wh = empty_warehouse

    # Check DimStatus
    df_status = wh.query("SELECT * FROM DimStatus ORDER BY status_key")
    assert len(df_status) == 3
    assert set(df_status["status_label"].values) == {"Pending", "In Progress", "Resolved"}

    # Check DimCategory
    df_category = wh.query("SELECT * FROM DimCategory ORDER BY category_key")
    assert len(df_category) == 5
    expected_categories = {"Wi-Fi", "Water", "Equipment", "Cleanliness", "Canteen"}
    assert set(df_category["category_name"].values) == expected_categories

    # Check DimCategory groups
    assert set(df_category["category_group"].values).issubset({"Infrastructure", "Services"})


def test_data_loading_populates_facts(populated_warehouse):
    """Test that data loading populates the fact table."""
    wh = populated_warehouse

    # Check FactCampusIssues row count
    df_facts = wh.query("SELECT COUNT(*) as cnt FROM FactCampusIssues")
    assert df_facts["cnt"].iloc[0] == 50

    # Check DimLocation has entries
    df_locations = wh.query("SELECT COUNT(*) as cnt FROM DimLocation")
    assert df_locations["cnt"].iloc[0] > 0


def test_foreign_key_integrity(populated_warehouse):
    """Test that all fact records have valid dimension keys."""
    wh = populated_warehouse

    # Check for orphaned keys (should be none)
    query = """
    SELECT COUNT(*) as orphaned_count
    FROM FactCampusIssues f
    WHERE f.date_key NOT IN (SELECT date_key FROM DimDate)
       OR f.location_key NOT IN (SELECT location_key FROM DimLocation)
       OR f.category_key NOT IN (SELECT category_key FROM DimCategory)
       OR f.status_key NOT IN (SELECT status_key FROM DimStatus)
    """
    df_orphaned = wh.query(query)
    assert df_orphaned["orphaned_count"].iloc[0] == 0, "Found orphaned foreign keys"


def test_resolution_hours_calculation(populated_warehouse):
    """Test that resolution_hours are correctly calculated for resolved issues."""
    wh = populated_warehouse

    # Get resolved issues with resolution_hours
    df_resolved = wh.query("""
        SELECT f.resolution_hours, s.status_label
        FROM FactCampusIssues f
        JOIN DimStatus s ON f.status_key = s.status_key
        WHERE s.status_label = 'Resolved' AND f.resolution_hours IS NOT NULL
    """)

    if len(df_resolved) > 0:
        # Check that all resolution_hours are positive
        assert (df_resolved["resolution_hours"] > 0).all(), "Found non-positive resolution hours"


def test_duplicate_prevention(populated_warehouse):
    """Test that duplicate report_ids are prevented."""
    wh = populated_warehouse

    # Count distinct report_ids vs total records
    df_check = wh.query("""
        SELECT COUNT(DISTINCT report_id) as distinct_ids, COUNT(*) as total_rows
        FROM FactCampusIssues
    """)

    distinct = df_check["distinct_ids"].iloc[0]
    total = df_check["total_rows"].iloc[0]
    assert distinct == total, "Found duplicate report_ids"


def test_text_preprocessing(populated_warehouse):
    """Test that descriptions have been preprocessed (lowercased, punctuation removed)."""
    wh = populated_warehouse

    # Get a sample of descriptions
    df_sample = wh.query("SELECT description FROM FactCampusIssues LIMIT 10")

    for desc in df_sample["description"].values:
        if desc:
            # Check that descriptions are lowercase
            assert desc == desc.lower(), f"Description not lowercased: {desc}"
            # Check no special punctuation remains (except spaces)
            assert not any(c in desc for c in "!@#$%^&*()"), f"Special characters found: {desc}"


def test_query_method(populated_warehouse):
    """Test the query method returns pandas DataFrame."""
    wh = populated_warehouse

    result = wh.query("SELECT * FROM FactCampusIssues LIMIT 5")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 5
    assert "report_id" in result.columns


def test_empty_warehouse_queries(empty_warehouse):
    """Test that queries on empty warehouse don't crash."""
    wh = empty_warehouse

    # These should return empty DataFrames, not crash
    df1 = wh.query("SELECT * FROM FactCampusIssues")
    assert len(df1) == 0

    df2 = wh.query("SELECT COUNT(*) as cnt FROM FactCampusIssues")
    assert df2["cnt"].iloc[0] == 0

    # Join queries should also work
    df3 = wh.query("""
        SELECT c.category_name, COUNT(*) as cnt
        FROM FactCampusIssues f
        JOIN DimCategory c ON f.category_key = c.category_key
        GROUP BY c.category_name
    """)
    assert len(df3) == 0


def test_warehouse_close(populated_warehouse):
    """Test that closing the warehouse works correctly."""
    wh = populated_warehouse
    wh.close()

    # After close, connection should not work
    with pytest.raises(Exception):
        wh.query("SELECT * FROM FactCampusIssues")


def test_threading_safety(populated_warehouse):
    """Test that warehouse can be safely accessed from multiple threads."""
    import threading

    wh = populated_warehouse
    results = []
    errors = []

    def query_in_thread():
        try:
            df = wh.query("SELECT COUNT(*) as cnt FROM FactCampusIssues")
            results.append(df["cnt"].iloc[0])
        except Exception as e:
            errors.append(str(e))

    threads = []
    for _ in range(5):
        t = threading.Thread(target=query_in_thread)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Threading errors: {errors}"
    assert all(cnt == results[0] for cnt in results), "Inconsistent query results across threads"
