# CampusPulse Quick Start Guide

## Prerequisites
- Windows 11
- Python 3.14+ (already installed at `.\.venv\Scripts\python.exe`)
- All dependencies in `requirements.txt` (already installed)

## 5-Minute Quick Start

### Step 1: Open PowerShell
Navigate to the project directory:
```powershell
cd C:\Users\KIIT\Documents\vscode\CampusPulse
```

### Step 2: Initialize (First Time Only)
```powershell
.\.venv\Scripts\python.exe setup.py
```
**Expected Output:**
- Generates 400 synthetic campus issue records
- Creates SQLite warehouse with 5 tables
- Trains Naive Bayes classifier (93.8% accuracy)
- Saves trained models
- **Total Time:** ~30 seconds

### Step 3: Launch Dashboard
```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.

  URL: http://localhost:8501
```

### Step 4: View in Browser
Open browser and navigate to: **http://localhost:8501/**

## Dashboard Navigation

### 1. Dashboard Overview (Default Page)
- **Total Reports:** 400 records
- **Pending:** 113 issues awaiting resolution
- **Resolved:** 205 completed issues (avg 82.7 hours)
- **Charts:**
  - Issues by Category (bar chart)
  - Top 10 Locations (horizontal bar chart)
  - Trend over time (line chart)

### 2. Report Submission
- **Form Fields:**
  - Issue Description (free text)
  - Category dropdown (Wi-Fi, Water, Cleanliness, Canteen, Equipment)
  - Location dropdown (11 campus buildings)
- **Note:** Form submission is for demonstration; saved reports are not persisted to database

### 3. Data Analysis
- **Status Distribution** - Pie chart of Pending/In Progress/Resolved
- **Category-Location Heatmap** - Shows issue concentrations by location and category

### 4. Mining Results
- **Train Classification Model** - Trains Naive Bayes on 320 records, tests on 80, shows accuracy
- **Perform Clustering** - K-Means with 3 clusters, displays silhouette score
- **Mine Association Rules** - Apriori algorithm finds category co-occurrence patterns
- **Test Prediction** - Enter issue description to predict category:
  - Example: "WiFi not working" → Predicted: Wi-Fi
  - Example: "Floor is dirty" → Predicted: Cleanliness

### 5. Warehouse Explorer
- **Recent Reports** - Browse last 20 issues with full details
- **Custom SQL Query** - Write your own SQL to explore raw data
  - Example queries:
    ```sql
    SELECT category_name, COUNT(*) FROM FactCampusIssues f
    JOIN DimCategory c ON f.category_key = c.category_key
    GROUP BY category_name ORDER BY COUNT(*) DESC;
    ```

## Demonstration Scenario (For Professor)

### Total Time: ~5 minutes

1. **Start the dashboard** (30 seconds)
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run dashboard.py
   ```

2. **View Dashboard Overview** (30 seconds)
   - Show total reports: 400
   - Show category distribution
   - Show location heatmap
   - Show trend over time

3. **Run Mining Algorithms** (2 minutes)
   - Click "Train Classification Model" → Show 93.8% accuracy
   - Click "Perform Clustering" → Show silhouette score
   - Click "Mine Association Rules" → Show generated rules
   - Test prediction: "WiFi not working" → Shows predicted category

4. **Explore Data** (1 minute)
   - Navigate to Data Analysis → Show status/category charts
   - Navigate to Warehouse Explorer → Browse recent reports
   - Show custom SQL query capability

5. **Key Talking Points:**
   - **Data Pipeline:** Raw data → ETL → Star schema → Analytics
   - **Machine Learning:** Text classification (93.8% accuracy), clustering, association rules
   - **Web Interface:** Interactive dashboard with 5 sections
   - **Database:** SQLite with 400 real-looking synthetic records
   - **Data Quality:** No orphaned records, proper foreign keys

## Troubleshooting

### Dashboard Won't Start
**Error:** `ModuleNotFoundError: No module named 'streamlit'`
**Fix:** 
```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

### Threading Error
**Error:** `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`
**Status:** ✅ FIXED - All threading issues have been resolved

### Database Corruption
**Error:** `database disk image malformed`
**Fix:**
```powershell
rm data/campus_issues.db
.\.venv\Scripts\python.exe setup.py
```

### Port Already in Use
**Error:** `OSError: [Errno 48] Address already in use`
**Fix:**
```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8502
```

## Run Tests

```powershell
# All tests
.\.venv\Scripts\pytest tests/ -v

# Specific test suites
.\.venv\Scripts\pytest tests/test_warehouse.py -v
.\.venv\Scripts\pytest tests/test_mining.py -v
.\.venv\Scripts\pytest tests/test_integration.py -v
```

**Expected Result:** 32 passed tests

## Project Files

```
CampusPulse/
├── dashboard.py                 # Streamlit application
├── setup.py                     # Initialization script
├── requirements.txt             # Python dependencies
├── FIXES_AND_TESTING_REPORT.md  # Detailed testing report
├── README.md                    # Original documentation
├── PROJECT_SUMMARY.md           # Project overview
│
├── data/
│   ├── campus_issues.csv        # 400 synthetic records
│   └── campus_issues.db         # SQLite warehouse
│
├── src/
│   ├── generate_data.py         # Synthetic data generator
│   ├── warehouse.py             # ETL and star schema
│   └── mining.py                # Data mining algorithms
│
├── models/
│   ├── classifier.pkl           # Trained Naive Bayes model
│   └── vectorizer.pkl           # TF-IDF vectorizer
│
└── tests/
    ├── conftest.py              # Test fixtures
    ├── test_warehouse.py        # 11 warehouse tests
    ├── test_mining.py           # 17 mining tests
    └── test_integration.py      # 4 integration tests
```

## Key Statistics

| Metric | Value |
|--------|-------|
| Total Records | 400 |
| Database Tables | 5 (star schema) |
| Classifier Accuracy | 93.8% |
| Silhouette Score (K-Means) | 0.542 |
| Association Rules Generated | 8+ |
| Test Suite | 32 tests, 100% pass |
| Threading Safety | Verified (5 threads) |
| Foreign Key Integrity | 100% valid |

## Support

For issues or questions, refer to:
- `FIXES_AND_TESTING_REPORT.md` - Detailed technical report
- `README.md` - Original project documentation
- `PROJECT_SUMMARY.md` - Academic overview

## Next Steps (After Presentation)

1. **Backup your work:**
   ```powershell
   # Database and models are already in the repository
   # No additional backup needed
   ```

2. **Prepare presentation:**
   - Review slides in `CampusPulse_PPT/CampusPulse_Report.pptx`
   - Consider adding screenshots from dashboard
   - Highlight the 32 passing tests

3. **Expected Questions & Answers:**
   - **Q:** How do you handle threading in Streamlit?
     - **A:** SQLite connection with `check_same_thread=False` + lock protection
   - **Q:** What's the classifier accuracy?
     - **A:** 93.8% on held-out test set (80 records)
   - **Q:** Can it handle large datasets?
     - **A:** Demonstrated with 400 records; would need database migration for production scale
   - **Q:** Is the data real?
     - **A:** Synthetic but realistic (labeled "generated" in code)

---

**CampusPulse is ready for academic presentation!** 🎓
