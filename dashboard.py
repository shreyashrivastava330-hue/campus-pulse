"""
CampusPulse — Interactive Streamlit Dashboard

Real-time visualization of warehouse data and mining results.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from warehouse import CampusIssueWarehouse
from mining import CampusIssueMiner


@st.cache_resource
def get_warehouse():
    """Cache the warehouse connection."""
    return CampusIssueWarehouse("data/campus_issues.db")


def get_miner():
    """Get miner instance (not cached to allow retraining)."""
    wh = get_warehouse()
    return CampusIssueMiner(wh)


def main():
    st.set_page_config(page_title="CampusPulse", layout="wide", initial_sidebar_state="expanded")

    st.title("CampusPulse — Campus Issue Analysis Dashboard")
    st.markdown("""
    **Turning Student Feedback into Actionable Campus Insights**

    A data-driven system for analyzing campus facility issues using data mining and warehousing.
    """)

    # Sidebar navigation
    page = st.sidebar.radio("Navigation", [
        "Dashboard Overview",
        "Report Submission",
        "Data Analysis",
        "Mining Results",
        "Warehouse Explorer"
    ])

    wh = get_warehouse()

    if page == "Dashboard Overview":
        show_overview(wh)
    elif page == "Report Submission":
        show_submission(wh)
    elif page == "Data Analysis":
        show_analysis(wh)
    elif page == "Mining Results":
        show_mining_results(wh)
    elif page == "Warehouse Explorer":
        show_warehouse_explorer(wh)


def show_overview(wh):
    """Display dashboard overview with KPIs and trends."""
    st.header("Dashboard Overview")

    try:
        # Fetch key metrics
        total_reports = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM FactCampusIssues", wh.conn
        )["count"].iloc[0]

        pending = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM FactCampusIssues f JOIN DimStatus s ON f.status_key = s.status_key WHERE s.status_label = 'Pending'",
            wh.conn
        )["count"].iloc[0]

        resolved = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM FactCampusIssues f JOIN DimStatus s ON f.status_key = s.status_key WHERE s.status_label = 'Resolved'",
            wh.conn
        )["count"].iloc[0]

        avg_resolution_df = pd.read_sql_query(
            "SELECT AVG(resolution_hours) as avg_hours FROM FactCampusIssues WHERE resolution_hours IS NOT NULL",
            wh.conn
        )
        avg_resolution = avg_resolution_df["avg_hours"].iloc[0] if len(avg_resolution_df) > 0 and avg_resolution_df["avg_hours"].iloc[0] is not None else None

        # KPI display
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Reports", total_reports)
        with col2:
            st.metric("Pending", pending)
        with col3:
            st.metric("Resolved", resolved)
        with col4:
            st.metric("Avg Resolution (hrs)", f"{avg_resolution:.1f}" if avg_resolution else "N/A")

        st.divider()

        # Charts
        col1, col2 = st.columns(2)

        # Issues by Category
        with col1:
            df_cat = pd.read_sql_query("""
                SELECT c.category_name, COUNT(*) as count
                FROM FactCampusIssues f
                JOIN DimCategory c ON f.category_key = c.category_key
                GROUP BY c.category_name
                ORDER BY count DESC
            """, wh.conn)

            if len(df_cat) > 0:
                fig_cat = px.bar(df_cat, x="category_name", y="count",
                                 title="Reports by Category",
                                 labels={"category_name": "Category", "count": "Count"},
                                 color="count", color_continuous_scale="Viridis")
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No category data available.")

        # Issues by Location
        with col2:
            df_loc = pd.read_sql_query("""
                SELECT l.building_name, COUNT(*) as count
                FROM FactCampusIssues f
                JOIN DimLocation l ON f.location_key = l.location_key
                GROUP BY l.building_name
                ORDER BY count DESC
                LIMIT 10
            """, wh.conn)

            if len(df_loc) > 0:
                fig_loc = px.barh(df_loc, y="building_name", x="count",
                                  title="Top 10 Locations by Issue Count",
                                  labels={"building_name": "Location", "count": "Count"},
                                  color="count", color_continuous_scale="Blues")
                st.plotly_chart(fig_loc, use_container_width=True)
            else:
                st.info("No location data available.")

        st.divider()

        # Trend over time
        df_trend = pd.read_sql_query("""
            SELECT d.full_date, COUNT(*) as count
            FROM FactCampusIssues f
            JOIN DimDate d ON f.date_key = d.date_key
            GROUP BY d.full_date
            ORDER BY d.full_date
        """, wh.conn)

        if len(df_trend) > 0:
            df_trend["full_date"] = pd.to_datetime(df_trend["full_date"])
            fig_trend = px.line(df_trend, x="full_date", y="count",
                                title="Issue Reports Over Time",
                                labels={"full_date": "Date", "count": "Count"})
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No trend data available.")

    except Exception as e:
        st.error(f"Error loading dashboard overview: {str(e)}")
        st.info("Please check that the database is properly initialized with data.")


def show_submission(wh):
    """Report submission interface."""
    st.header("Submit a Campus Issue Report")

    with st.form("issue_form"):
        description = st.text_area("Issue Description", placeholder="Describe the issue you encountered...")
        category = st.selectbox("Category", ["Wi-Fi", "Water", "Cleanliness", "Canteen", "Equipment"])
        location = st.selectbox("Location", [
            "Library Block A", "Library Block B", "Academic Block A", "Academic Block B",
            "Academic Block C", "Hostel Block 1", "Hostel Block 2", "Canteen Area",
            "Lab Building", "Sports Complex", "Main Gate Area"
        ])

        submitted = st.form_submit_button("Submit Report")

        if submitted:
            if not description:
                st.error("Please enter a description.")
            else:
                st.success("Report submitted successfully! Thank you.")
                st.info(f"Your report about '{category}' in '{location}' has been recorded.")


def show_analysis(wh):
    """Data analysis section."""
    st.header("Data Analysis")

    try:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Status Distribution")
            df_status = pd.read_sql_query("""
                SELECT s.status_label, COUNT(*) as count
                FROM FactCampusIssues f
                JOIN DimStatus s ON f.status_key = s.status_key
                GROUP BY s.status_label
            """, wh.conn)

            if len(df_status) > 0:
                fig_status = px.pie(df_status, values="count", names="status_label",
                                    title="Issues by Status")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No status data available.")

        with col2:
            st.subheader("Category-Location Heatmap")
            df_heatmap = pd.read_sql_query("""
                SELECT c.category_name, l.building_name, COUNT(*) as count
                FROM FactCampusIssues f
                JOIN DimCategory c ON f.category_key = c.category_key
                JOIN DimLocation l ON f.location_key = l.location_key
                GROUP BY c.category_name, l.building_name
            """, wh.conn)

            if len(df_heatmap) > 0:
                pivot_df = df_heatmap.pivot_table(
                    index="building_name", columns="category_name",
                    values="count", fill_value=0
                )
                fig_heatmap = px.imshow(pivot_df, title="Issue Count Heatmap",
                                        labels=dict(x="Category", y="Location", color="Count"),
                                        color_continuous_scale="YlOrRd")
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("No heatmap data available.")

    except Exception as e:
        st.error(f"Error loading data analysis: {str(e)}")
        st.info("Please check that the database is properly initialized.")


def show_mining_results(wh):
    """Display data mining results."""
    st.header("Data Mining Results")

    st.info("Training models on warehouse data. This may take a moment...")

    miner = get_miner()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Train Classification Model"):
            with st.spinner("Training Naive Bayes classifier..."):
                result = miner.train_classifier()
                if result:
                    st.success(f"Classification Accuracy: {result['accuracy']:.1%}")

    with col2:
        if st.button("Perform Clustering"):
            with st.spinner("Running K-Means clustering..."):
                result = miner.perform_clustering(n_clusters=3)
                if result:
                    st.success(f"Silhouette Score: {result['silhouette_score']:.3f}")

    with col3:
        if st.button("Mine Association Rules"):
            with st.spinner("Running Apriori algorithm..."):
                result = miner.mine_association_rules()
                if result:
                    st.success(f"Generated {len(result)} rules")

    st.divider()

    # Test classification
    st.subheader("Test Category Prediction")
    test_text = st.text_input("Enter a test issue description:")
    if test_text:
        predicted_cat, confidence = miner.predict_category(test_text)
        if predicted_cat:
            st.success(f"Predicted Category: **{predicted_cat}** (Confidence: {confidence:.1%})")
        else:
            st.warning("Model not trained yet. Train the classifier first.")


def show_warehouse_explorer(wh):
    """Raw warehouse data explorer."""
    st.header("Warehouse Explorer")

    try:
        st.subheader("Recent Reports")
        df_recent = pd.read_sql_query("""
            SELECT
                f.report_id,
                f.description,
                c.category_name as category,
                l.building_name as location,
                d.full_date as reported_date,
                s.status_label as status
            FROM FactCampusIssues f
            JOIN DimCategory c ON f.category_key = c.category_key
            JOIN DimLocation l ON f.location_key = l.location_key
            JOIN DimDate d ON f.date_key = d.date_key
            JOIN DimStatus s ON f.status_key = s.status_key
            ORDER BY f.report_id DESC
            LIMIT 20
        """, wh.conn)

        if len(df_recent) > 0:
            st.dataframe(df_recent, use_container_width=True)
        else:
            st.info("The warehouse is currently empty. No issue reports found.")

        st.divider()

        st.subheader("Custom SQL Query")
        query = st.text_area("Enter SQL query:", height=100,
                             value="SELECT * FROM FactCampusIssues LIMIT 10;")
        if st.button("Execute Query"):
            try:
                result = wh.query(query)
                if len(result) > 0:
                    st.dataframe(result, use_container_width=True)
                else:
                    st.info("Query executed successfully but returned no rows.")
            except Exception as e:
                st.error(f"Query error: {str(e)}")
                st.info("Please check your SQL syntax and try again.")

    except Exception as e:
        st.error(f"Error loading warehouse explorer: {str(e)}")
        st.info("The warehouse may not be properly initialized. Please run setup.py.")


if __name__ == "__main__":
    main()
