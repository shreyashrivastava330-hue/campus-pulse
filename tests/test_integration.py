"""
Integration tests for CampusPulse - end-to-end workflow testing.
"""

import pytest
import os
import tempfile
import subprocess
import sys


def test_setup_script_creates_artifacts():
    """Test that setup.py creates all required artifacts."""
    # Create a temporary directory for this test
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()

    try:
        os.chdir(test_dir)

        # Create minimal project structure
        os.makedirs("src", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("models", exist_ok=True)

        # Copy source files
        import shutil
        shutil.copy(os.path.join(original_dir, "src", "generate_data.py"), "src/")
        shutil.copy(os.path.join(original_dir, "src", "warehouse.py"), "src/")
        shutil.copy(os.path.join(original_dir, "src", "mining.py"), "src/")
        shutil.copy(os.path.join(original_dir, "setup.py"), ".")

        # Run setup.py
        result = subprocess.run(
            [sys.executable, "setup.py"],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Check that it completed successfully
        assert result.returncode == 0, f"setup.py failed: {result.stderr}"

        # Verify artifacts were created
        assert os.path.exists("data/campus_issues.csv"), "CSV not generated"
        assert os.path.exists("data/campus_issues.db"), "Database not created"
        assert os.path.exists("models/classifier.pkl"), "Classifier not trained"
        assert os.path.exists("models/vectorizer.pkl"), "Vectorizer not trained"

        # Verify CSV has data
        with open("data/campus_issues.csv") as f:
            lines = f.readlines()
            assert len(lines) > 1, "CSV is empty"  # Header + at least 1 row

    finally:
        os.chdir(original_dir)
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)


def test_warehouse_etl_idempotency():
    """Test that warehouse prevents duplicate report_ids via UNIQUE constraint."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    from warehouse import CampusIssueWarehouse
    from generate_data import generate_dataset
    import tempfile
    import sqlite3

    # Create temp files
    fd_db, db_path = tempfile.mkstemp(suffix=".db")
    fd_csv, csv_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd_db)
    os.close(fd_csv)

    try:
        # Generate test data
        generate_dataset(50, csv_path)

        # Load once
        wh = CampusIssueWarehouse(db_path)
        wh.load_data(csv_path)

        # Count records
        df_count1 = wh.query("SELECT COUNT(*) as cnt FROM FactCampusIssues")
        count1 = df_count1["cnt"].iloc[0]

        # Try to load again - should raise UNIQUE constraint error (this is correct behavior)
        try:
            wh.load_data(csv_path)
            # If we reach here, check that no duplicates were added
            df_count2 = wh.query("SELECT COUNT(*) as cnt FROM FactCampusIssues")
            count2 = df_count2["cnt"].iloc[0]
            assert count1 == count2, "Duplicates were added when loading twice"
        except sqlite3.IntegrityError as e:
            # UNIQUE constraint failure is expected and correct
            assert "UNIQUE constraint failed" in str(e)

        wh.close()

    finally:
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except:
            pass
        try:
            if os.path.exists(csv_path):
                os.unlink(csv_path)
        except:
            pass


def test_mining_pipeline_on_real_warehouse():
    """Test that all mining functions work on real warehouse with data."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    from warehouse import CampusIssueWarehouse
    from mining import CampusIssueMiner
    from generate_data import generate_dataset
    import tempfile

    fd_db, db_path = tempfile.mkstemp(suffix=".db")
    fd_csv, csv_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd_db)
    os.close(fd_csv)

    try:
        # Generate and load data
        generate_dataset(100, csv_path)
        wh = CampusIssueWarehouse(db_path)
        wh.load_data(csv_path)

        # Test all mining functions
        miner = CampusIssueMiner(wh)

        # Classification
        cls_result = miner.train_classifier()
        assert cls_result is not None, "Classification failed"

        # Clustering
        clust_result = miner.perform_clustering(n_clusters=3)
        assert clust_result is not None, "Clustering failed"

        # Association rules
        apriori_result = miner.mine_association_rules()
        # Apriori might return None if no rules - that's OK

        # Prediction
        category, confidence = miner.predict_category("WiFi not working")
        assert category is not None, "Prediction failed"
        assert 0 <= confidence <= 1

        wh.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(csv_path):
            os.unlink(csv_path)


def test_concurrent_warehouse_access():
    """Test that warehouse handles concurrent access safely."""
    import threading

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    from warehouse import CampusIssueWarehouse
    from generate_data import generate_dataset
    import tempfile

    fd_db, db_path = tempfile.mkstemp(suffix=".db")
    fd_csv, csv_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd_db)
    os.close(fd_csv)

    try:
        # Setup
        generate_dataset(50, csv_path)
        wh = CampusIssueWarehouse(db_path)
        wh.load_data(csv_path)

        # Create shared miner (simulating Streamlit cache)
        from mining import CampusIssueMiner
        miner = CampusIssueMiner(wh)
        miner.train_classifier()

        results = []
        errors = []

        def query_and_predict(thread_id):
            try:
                # Query warehouse
                df = wh.query("SELECT COUNT(*) FROM FactCampusIssues")
                # Use miner
                cat, conf = miner.predict_category("Test issue from thread")
                results.append((thread_id, cat, conf))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Run queries from multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=query_and_predict, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Threading errors: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"

        wh.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(csv_path):
            os.unlink(csv_path)
