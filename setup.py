"""
CampusPulse Setup and Initialization Script

Generates dataset, builds warehouse, trains models, and prepares the system.
"""

import os
import sys
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from generate_data import generate_dataset
from warehouse import CampusIssueWarehouse
from mining import CampusIssueMiner


def setup():
    """Complete setup workflow."""
    print("\n" + "="*70)
    print("CampusPulse — Setup and Initialization")
    print("="*70)

    # 1. Create directories
    print("\n[1/5] Creating project directories...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    print("  OK: data/, models/ directories ready")

    # 2. Generate synthetic dataset
    print("\n[2/5] Generating synthetic dataset...")
    if os.path.exists("data/campus_issues.csv"):
        print("  SKIP: campus_issues.csv already exists")
    else:
        generate_dataset(400, "data/campus_issues.csv")
        print("  OK: Generated 400 synthetic records")

    # 3. Build data warehouse
    print("\n[3/5] Building SQLite data warehouse...")
    db_path = "data/campus_issues.db"
    if os.path.exists(db_path):
        print(f"  OVERWRITE: Removing existing {db_path}...")
        os.remove(db_path)

    wh = CampusIssueWarehouse(db_path)
    wh.load_data("data/campus_issues.csv")
    print("  OK: Warehouse created and loaded")

    # 4. Train data mining models
    print("\n[4/5] Training data mining models...")
    miner = CampusIssueMiner(wh)

    print("\n  [4a] Training Naive Bayes classifier...")
    cls_result = miner.train_classifier(train_size=0.8)
    if cls_result:
        miner.save_models("models")
        print(f"       Accuracy: {cls_result['accuracy']:.3f}")

    print("\n  [4b] Performing K-Means clustering...")
    clust_result = miner.perform_clustering(n_clusters=3)
    if clust_result:
        print(f"       Silhouette Score: {clust_result['silhouette_score']:.3f}")

    print("\n  [4c] Mining association rules...")
    rules = miner.mine_association_rules(min_support=0.05, min_confidence=0.3)
    if rules:
        print(f"       Generated {len(rules)} association rules")

    # 5. Summary and next steps
    print("\n[5/5] Setup Complete!")
    print("="*70)
    print("\nProject Structure:")
    print("  data/")
    print("    campus_issues.csv        (400 synthetic records)")
    print("    campus_issues.db         (SQLite star-schema warehouse)")
    print("  src/")
    print("    generate_data.py         (Dataset generation)")
    print("    warehouse.py             (ETL and warehouse)")
    print("    mining.py                (Data mining algorithms)")
    print("  models/")
    print("    classifier.pkl           (Trained Naive Bayes model)")
    print("    vectorizer.pkl           (TF-IDF vectorizer)")
    print("  dashboard.py               (Streamlit interactive dashboard)")
    print("  setup.py                   (This file)")
    print("  README.md                  (Documentation)")

    print("\n" + "="*70)
    print("Next Steps:")
    print("="*70)
    print("\n1. Run the interactive dashboard:")
    print("   streamlit run dashboard.py")
    print("\n2. Explore the warehouse directly:")
    print("   python -c \"from src.warehouse import CampusIssueWarehouse;")
    print("   wh = CampusIssueWarehouse('data/campus_issues.db');")
    print("   print(wh.query('SELECT * FROM FactCampusIssues LIMIT 5'))\"")
    print("\n3. Review the presentation:")
    print("   Open: CampusPulse_Report.pptx (in ../CampusPulse_PPT/)")
    print("\n" + "="*70)

    wh.close()


if __name__ == "__main__":
    setup()
