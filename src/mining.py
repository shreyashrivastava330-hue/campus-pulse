"""
CampusPulse — Data Mining Algorithms Module

Implements text classification (Naive Bayes), clustering (K-Means),
and association rule mining (Apriori).
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from mlxtend.frequent_patterns import apriori, association_rules
import pickle
import os


class CampusIssueMiner:
    """Data mining suite for campus issue analysis."""

    def __init__(self, warehouse_obj):
        self.wh = warehouse_obj
        self.classifier = None
        self.vectorizer = None
        self.kmeans = None
        self.tfidf_matrix = None

    # ──── Text Classification: TF-IDF + Naive Bayes ────

    def train_classifier(self, train_size=0.8):
        """Train a Multinomial Naive Bayes classifier on TF-IDF features."""
        print("[Classification] Fetching data from warehouse...")
        df = self.wh.query("""
            SELECT f.description, c.category_name as category
            FROM FactCampusIssues f
            JOIN DimCategory c ON f.category_key = c.category_key
            WHERE f.description IS NOT NULL
        """)

        if len(df) < 10:
            print("[Classification] Insufficient data for training.")
            return None

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            df["description"], df["category"],
            test_size=1 - train_size, random_state=42, stratify=df["category"]
        )

        print(f"[Classification] Training set: {len(X_train)}, Test set: {len(X_test)}")

        # TF-IDF vectorization (fitted on training data only)
        self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2), min_df=2)
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        X_test_tfidf = self.vectorizer.transform(X_test)

        # Train Multinomial Naive Bayes
        self.classifier = MultinomialNB()
        self.classifier.fit(X_train_tfidf, y_train)

        # Evaluate
        y_pred = self.classifier.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"[Classification] Accuracy: {accuracy:.3f}")
        print("[Classification] Classification Report:")
        print(classification_report(y_test, y_pred))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"[Classification] Confusion Matrix:\n{cm}")

        return {"accuracy": accuracy, "n_train": len(X_train), "n_test": len(X_test)}

    def predict_category(self, text):
        """Predict category for a new report."""
        if not self.classifier or not self.vectorizer:
            return None, 0.0

        try:
            if not text or not isinstance(text, str) or len(text.strip()) == 0:
                return None, 0.0

            text_tfidf = self.vectorizer.transform([text])
            prediction = self.classifier.predict(text_tfidf)[0]
            confidence = self.classifier.predict_proba(text_tfidf).max()
            return prediction, confidence
        except Exception as e:
            print(f"[Classification] Prediction error: {e}")
            return None, 0.0

    # ──── Clustering: K-Means ────

    def perform_clustering(self, n_clusters=3):
        """Apply K-Means clustering to report descriptions."""
        print(f"[Clustering] Fetching data from warehouse...")
        df = self.wh.query("""
            SELECT description FROM FactCampusIssues
            WHERE description IS NOT NULL
        """)

        if len(df) < n_clusters:
            print(f"[Clustering] Insufficient data for {n_clusters} clusters.")
            return None

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2), min_df=2)
        self.tfidf_matrix = vectorizer.fit_transform(df["description"])

        # K-Means clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df["cluster"] = self.kmeans.fit_predict(self.tfidf_matrix)

        # Silhouette score
        silhouette = silhouette_score(self.tfidf_matrix, df["cluster"])
        print(f"[Clustering] Silhouette Score: {silhouette:.3f}")

        # Print cluster summary
        for cluster_id in range(n_clusters):
            cluster_data = df[df["cluster"] == cluster_id]
            print(f"\n[Clustering] Cluster {cluster_id} (n={len(cluster_data)}):")
            if len(cluster_data) > 0:
                representative = cluster_data.iloc[0]["description"][:80]
                print(f"  Representative: {representative}...")

        return {"silhouette_score": silhouette, "n_clusters": n_clusters}

    # ──── Association Rule Mining: Apriori ────

    def mine_association_rules(self, min_support=0.05, min_confidence=0.3):
        """Generate association rules for category co-occurrences."""
        print("[Association Mining] Fetching data from warehouse...")

        # Group by location-week to form transactions
        df = self.wh.query("""
            SELECT
                l.building_name,
                CAST((JULIANDAY(d.full_date) - JULIANDAY('2026-01-01')) / 7 AS INTEGER) as week,
                c.category_name
            FROM FactCampusIssues f
            JOIN DimLocation l ON f.location_key = l.location_key
            JOIN DimCategory c ON f.category_key = c.category_key
            JOIN DimDate d ON f.date_key = d.date_key
        """)

        if len(df) == 0:
            print("[Association Mining] No data available.")
            return None

        # Create transactions
        transactions = []
        for (location, week), group in df.groupby(["building_name", "week"]):
            categories = sorted(group["category_name"].unique().tolist())
            if categories:
                transactions.append(categories)

        if len(transactions) < 2:
            print("[Association Mining] Insufficient transactions.")
            return None

        print(f"[Association Mining] Generated {len(transactions)} transactions")

        # Convert to one-hot encoding
        all_categories = sorted(set(cat for trans in transactions for cat in trans))
        one_hot_data = []
        for trans in transactions:
            row = {cat: (cat in trans) for cat in all_categories}
            one_hot_data.append(row)
        trans_df = pd.DataFrame(one_hot_data)

        # Apriori algorithm
        frequent_itemsets = apriori(trans_df, min_support=min_support, use_colnames=True)
        if len(frequent_itemsets) < 2:
            print("[Association Mining] No frequent itemsets found.")
            return None

        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        if len(rules) == 0:
            print("[Association Mining] No rules generated.")
            return None

        rules = rules.sort_values("lift", ascending=False)
        print(f"[Association Mining] Generated {len(rules)} rules:")
        for idx, rule in rules.head(10).iterrows():
            antecedent = ", ".join(list(rule["antecedents"]))
            consequent = ", ".join(list(rule["consequents"]))
            print(f"  {antecedent} => {consequent} | confidence: {rule['confidence']:.2f}, lift: {rule['lift']:.2f}")

        return rules.to_dict("records") if len(rules) > 0 else None

    def save_models(self, model_dir="models"):
        """Save trained models to disk."""
        os.makedirs(model_dir, exist_ok=True)
        if self.classifier:
            pickle.dump(self.classifier, open(f"{model_dir}/classifier.pkl", "wb"))
            pickle.dump(self.vectorizer, open(f"{model_dir}/vectorizer.pkl", "wb"))
            print(f"[Models] Saved to {model_dir}")

    def load_models(self, model_dir="models"):
        """Load trained models from disk."""
        try:
            self.classifier = pickle.load(open(f"{model_dir}/classifier.pkl", "rb"))
            self.vectorizer = pickle.load(open(f"{model_dir}/vectorizer.pkl", "rb"))
            print(f"[Models] Loaded from {model_dir}")
            return True
        except FileNotFoundError:
            print(f"[Models] No saved models found in {model_dir}")
            return False


if __name__ == "__main__":
    from warehouse import CampusIssueWarehouse

    wh = CampusIssueWarehouse("data/campus_issues.db")
    miner = CampusIssueMiner(wh)

    # Classification
    print("\n" + "="*60)
    print("TEXT CLASSIFICATION (Naive Bayes + TF-IDF)")
    print("="*60)
    miner.train_classifier()

    # Clustering
    print("\n" + "="*60)
    print("CLUSTERING (K-Means)")
    print("="*60)
    miner.perform_clustering(n_clusters=3)

    # Association Rules
    print("\n" + "="*60)
    print("ASSOCIATION RULE MINING (Apriori)")
    print("="*60)
    miner.mine_association_rules(min_support=0.05, min_confidence=0.3)

    wh.close()
