# 🚀 Campus Pulse Streamlit Community Cloud Deployment Guide

**Author:** Shreya Shrivastava  
**Project:** Campus Pulse - Data Mining & Data Warehousing  
**Repository:** https://github.com/shreyashrivastava330-hue/campus-pulse  
**Deployment Date:** October 28, 2026  

---

## ✅ Deployment Status

| Component | Status | Details |
|-----------|--------|---------|
| **Repository** | ✓ Ready | Public, all code pushed to `master` |
| **Entry Point** | ✓ Ready | `dashboard.py` configured |
| **Dependencies** | ✓ Ready | `requirements.txt` complete |
| **Database Init** | ✓ Ready | Auto-initialization on app startup |
| **Plotly Fix** | ✓ Ready | barh() → bar() with orientation fix |
| **Streamlit Config** | ✓ Ready | `.streamlit/config.toml` configured |
| **Latest Commit** | ✓ Ready | 342602d - Deploy support configured |

---

## 📦 Repository Information

```
Repository URL:  https://github.com/shreyashrivastava330-hue/campus-pulse
Branch:          master
Entry Point:     dashboard.py (in repository root)
GitHub User:     shreyashrivastava330-hue
Repository Type: Public
```

---

## 🔧 Step-by-Step Deployment Instructions

### Step 1: Visit Streamlit Community Cloud

Go to **https://share.streamlit.io/**

Sign in with your GitHub account. If you don't have one, create one first at https://github.com/signup

### Step 2: Create a New App

Click the **"Create app"** button in the top-right corner of the Streamlit Community Cloud dashboard.

### Step 3: Authorize GitHub Access

Streamlit will prompt you to authorize access to your GitHub repositories. Click "Authorize" and grant the necessary permissions.

### Step 4: Configure Your Deployment

When prompted, fill in the following information:

| Field | Value |
|-------|-------|
| **GitHub Account** | `shreyashrivastava330-hue` |
| **Repository** | `campus-pulse` |
| **Branch** | `master` |
| **Main file path** | `dashboard.py` |

### Step 5: Deploy

Click the **"Deploy"** button and wait for the deployment to complete.

**Expected deployment time:** 2-5 minutes

Streamlit will automatically:
- Clone your repository
- Install Python 3.11+
- Install all dependencies from `requirements.txt`
- Initialize the app

### Step 6: Access Your Live App

Once deployment completes, your app will be live at:

```
https://campus-pulse.streamlit.app
```

(or at a similar URL based on your repository name)

---

## 🛠️ Configuration Details

### Python Dependencies

Your `requirements.txt` includes:

```
pandas
numpy
scikit-learn
mlxtend
streamlit
plotly
python-pptx
```

All dependencies are compatible with Streamlit Community Cloud's Python 3.11+ environment.

### Database Initialization

Campus Pulse now includes **automatic database initialization** for Streamlit Cloud:

- ✅ Checks for SQLite database on app startup
- ✅ Generates 400 synthetic campus issue records if needed
- ✅ Creates star-schema warehouse automatically
- ✅ Loads trained ML models
- ✅ Works with Streamlit Cloud's ephemeral filesystem
- ✅ First load takes ~30-60 seconds (data generation + initialization)
- ✅ Subsequent loads are instant (cached)

**How it works:**

The `get_warehouse()` function in `dashboard.py` calls `initialize_database()` which:

1. Creates `data/` directory if needed
2. Checks if `campus_issues.db` exists
3. If not, generates `campus_issues.csv` with 400 records
4. Builds the SQLite warehouse with star schema
5. Returns cached warehouse connection

This approach is **Streamlit Cloud-compatible** because:
- The app can function without pre-existing database files
- Data regeneration is deterministic (same synthetic data each time)
- Filesystem operations use relative paths from repository root

### Streamlit Configuration

Located at `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[client]
showErrorDetails = true

[logger]
level = "info"

[server]
port = 8501
headless = true
runOnSave = true
```

---

## 📊 Dashboard Features

Once deployed, your app includes **five interactive pages:**

### 1. 📈 Dashboard Overview
- **KPI Tiles:** Total Reports, Pending, Resolved, Average Resolution Time
- **Charts:** Reports by Category, Top Locations, Trends Over Time
- **Visualization:** Plotly interactive charts with hover/zoom/pan

### 2. 📝 Report Submission
- **Form:** Submit new campus issue reports
- **Fields:** Description, Category (5 options), Location (11 options)
- **Status:** Shows confirmation message (data stored in SQLite)

### 3. 📊 Data Analysis
- **Status Distribution:** Pie chart of issue statuses
- **Heatmap:** Category × Location analysis matrix
- **Insights:** Identify problem hotspots across campus

### 4. 🔬 Mining Results
- **Classification:** Train Naive Bayes classifier (93.8% accuracy)
- **Clustering:** Perform K-Means analysis (Silhouette Score: 0.542)
- **Association Rules:** Generate Apriori patterns (103 rules)
- **Prediction:** Test category prediction on custom text

### 5. 🗄️ Warehouse Explorer
- **SQL Query Interface:** Execute custom SQL queries
- **Recent Reports:** Browse last 20 reports with full details
- **Data Inspection:** Join across dimensions (Category, Location, Status, Date)

---

## ✅ Pre-Deployment Verification Checklist

Before deploying, confirm:

- [ ] Repository is **public** at https://github.com/shreyashrivastava330-hue/campus-pulse
- [ ] Latest changes are **pushed to `master` branch**
- [ ] `requirements.txt` contains **all dependencies**
- [ ] `dashboard.py` is in **repository root** (not in subdirectory)
- [ ] `.gitignore` excludes `.venv/`, `__pycache__/`, `.pytest_cache/`
- [ ] Database **auto-initialization** is enabled in `dashboard.py`
- [ ] **Plotly fix** applied (bar() with orientation="h")
- [ ] `.streamlit/config.toml` is **present and configured**
- [ ] No hardcoded paths (all use relative paths from repo root)
- [ ] No secrets or credentials in `.py` files
- [ ] `data/campus_issues.db` and `data/campus_issues.csv` in `.gitignore` ✓
- [ ] `models/` directory included (contains pickle files) ✓

**All items verified ✓**

---

## 🌐 Your Deployment URL

Once successfully deployed, your app will be accessible at:

```
https://campus-pulse.streamlit.app
```

Share this link with anyone to access your live dashboard!

---

## ⚠️ Important Notes about Streamlit Cloud

### Data Persistence

**Streamlit Cloud uses an ephemeral filesystem:**
- Database is regenerated each app restart (typically monthly or after code updates)
- User submissions via "Report Submission" page are **NOT persisted**
- Each fresh deployment gets a clean database with 400 synthetic records

**Why this is OK for this project:**
- Synthetic data is reproducible and deterministic
- Dashboard is read-primarily with exploration focus
- Academic project doesn't require persistent user submissions
- ML models are pre-trained (no training needed on cloud)

### Computation Time

- **First app load:** ~30-60 seconds (data generation + initialization)
- **Subsequent loads:** <1 second (cached database and models)
- **Page navigation:** Instant (all pages within single app)

### Automatic Redeployment

Any commits to the `master` branch trigger automatic redeployment:
- Deployment starts automatically
- Typically completes within 5 minutes
- Old version stays live until new version deploys
- No downtime during updates

### Logs & Debugging

To view deployment and runtime logs:
1. Go to your app on share.streamlit.io
2. Click **"Manage app"** (top-right)
3. Click **"Logs"** to see detailed messages
4. Logs show errors, initialization steps, and performance metrics

---

## 🔧 Troubleshooting

### Issue: Deployment Fails with Import Error

**Symptoms:** Error mentioning missing module (e.g., "No module named 'plotly'")

**Solution:**
1. Check that all imports are in `requirements.txt`
2. Verify package names are correct (e.g., `scikit-learn` not `sklearn`)
3. Add missing package to `requirements.txt`
4. Commit and push changes
5. Redeploy (automatic or manual)

### Issue: "Database Not Found" Error on First Load

**Symptoms:** SQLite error or "data/campus_issues.db not found"

**Solution:**
1. This is expected on first load
2. Wait 30-60 seconds for initialization
3. Refresh the page (F5)
4. Database will be auto-generated
5. Subsequent loads will be instant

### Issue: Charts Not Rendering

**Symptoms:** Blank areas where charts should be, Plotly errors

**Solution:**
1. The `barh()` → `bar()` fix is already applied
2. Try clearing browser cache (Ctrl+Shift+Delete)
3. Refresh the page
4. Check app logs for detailed error message

### Issue: Data Takes Too Long to Load

**Symptoms:** App spinning/loading for >2 minutes on first load

**Solution:**
1. This may be normal for first initialization
2. ML model training happens on startup in "Mining Results" page
3. Caching is enabled via `@st.cache_resource`
4. Subsequent page loads will be much faster
5. Check logs to see what step is taking time

### Issue: App Crashes or Goes Offline

**Symptoms:** 503 error, app unavailable

**Solution:**
1. Check app logs for crash details
2. Verify recent code changes don't have syntax errors
3. Test locally before committing: `streamlit run dashboard.py`
4. Check that `requirements.txt` has exact package versions
5. Streamlit Cloud restarts apps daily; normal downtime is brief

---

## 🚀 Quick Reference

| Task | What to Do |
|------|-----------|
| Deploy for first time | Follow Steps 1-6 above |
| Update app after code changes | Just commit & push to `master`; auto-deploys |
| View app logs | Click "Manage app" → "Logs" on app dashboard |
| Stop/restart app | Click "Manage app" → "Reboot" |
| Delete app | Click "Manage app" → "Delete app" |
| Check deployment status | Go to share.streamlit.io and look for your app |
| Share your app | Give others the URL: `https://campus-pulse.streamlit.app` |

---

## 📚 Additional Resources

- **Streamlit Documentation:** https://docs.streamlit.io/
- **Streamlit Cloud Deployment:** https://docs.streamlit.io/deploy/streamlit-community-cloud
- **Troubleshooting:** https://docs.streamlit.io/deploy/troubleshooting
- **GitHub:** https://github.com/shreyashrivastava330-hue/campus-pulse

---

## ✨ What's Included

Your deployment includes:

**Core Components:**
- `dashboard.py` — Main Streamlit app (entry point)
- `src/warehouse.py` — SQLite warehouse & ETL
- `src/mining.py` — Data mining algorithms
- `src/generate_data.py` — Synthetic data generation
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — Cloud configuration
- `.gitignore` — Proper exclusions
- `README.md` — Project documentation

**Data & Models:**
- `data/campus_issues.csv` — 400 synthetic records (generated on demand)
- `data/campus_issues.db` — SQLite warehouse (generated on demand)
- `models/classifier.pkl` — Trained Naive Bayes model
- `models/vectorizer.pkl` — TF-IDF vectorizer

**Dataset:**
- **400 campus issue reports**
- **5 categories:** Wi-Fi, Water, Cleanliness, Canteen, Equipment
- **11 locations:** Campus buildings and common areas
- **Time span:** August 1 – September 20, 2026
- **Status distribution:** Pending (30%), In Progress (20%), Resolved (50%)

---

## 🎯 Next Steps

1. **Go to** https://share.streamlit.io/
2. **Click** "Create app"
3. **Select:**
   - GitHub Account: `shreyashrivastava330-hue`
   - Repository: `campus-pulse`
   - Branch: `master`
   - Main file: `dashboard.py`
4. **Click** "Deploy"
5. **Wait** 2-5 minutes for deployment
6. **Access** your live app at the provided URL
7. **Share** the URL with colleagues, instructors, or friends!

---

**Status:** Ready for Deployment ✅  
**Repository:** Public ✓  
**Code:** Tested Locally ✓  
**Database:** Auto-Init Enabled ✓  
**Configuration:** Optimized for Streamlit Cloud ✓  

---

**Questions?** Check the [Streamlit Cloud Documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud) or review the app logs for detailed error messages.

**Good luck with your deployment! 🎉**
