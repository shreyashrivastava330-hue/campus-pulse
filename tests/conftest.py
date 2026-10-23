"""
Pytest configuration and fixtures for CampusPulse testing.
"""

import pytest
import tempfile
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from warehouse import CampusIssueWarehouse
from generate_data import generate_dataset


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def empty_warehouse(temp_db):
    """Create an empty warehouse with schema but no data."""
    wh = CampusIssueWarehouse(temp_db)
    wh.load_dimensions()
    yield wh
    wh.close()


@pytest.fixture
def populated_warehouse(temp_db):
    """Create a warehouse with synthetic data."""
    # Generate temporary CSV
    fd, csv_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)

    try:
        # Generate 50 synthetic records for faster testing
        generate_dataset(50, csv_path)

        # Load into warehouse
        wh = CampusIssueWarehouse(temp_db)
        wh.load_data(csv_path)
        yield wh
        wh.close()
    finally:
        if os.path.exists(csv_path):
            os.unlink(csv_path)


@pytest.fixture
def full_warehouse(temp_db):
    """Create a warehouse with full 400-record synthetic dataset."""
    # Generate temporary CSV
    fd, csv_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)

    try:
        # Generate full 400 synthetic records
        generate_dataset(400, csv_path)

        # Load into warehouse
        wh = CampusIssueWarehouse(temp_db)
        wh.load_data(csv_path)
        yield wh
        wh.close()
    finally:
        if os.path.exists(csv_path):
            os.unlink(csv_path)
