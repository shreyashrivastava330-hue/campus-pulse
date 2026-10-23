"""
Test suite for mining.py - Data mining algorithms.
"""

import pytest
from mining import CampusIssueMiner


class TestNaiveBayesClassification:
    """Tests for Naive Bayes text classification."""

    def test_classifier_trains_on_full_data(self, full_warehouse):
        """Test that classifier trains successfully on full dataset."""
        miner = CampusIssueMiner(full_warehouse)
        result = miner.train_classifier(train_size=0.8)

        assert result is not None, "Classifier training returned None"
        assert "accuracy" in result
        assert "n_train" in result
        assert "n_test" in result
        assert 0 <= result["accuracy"] <= 1, "Accuracy out of valid range"
        assert result["n_train"] > 0
        assert result["n_test"] > 0

    def test_classifier_returns_none_on_insufficient_data(self, empty_warehouse):
        """Test that classifier returns None when data is insufficient."""
        miner = CampusIssueMiner(empty_warehouse)
        result = miner.train_classifier()

        assert result is None, "Expected None for insufficient data"

    def test_prediction_before_training(self):
        """Test that prediction returns (None, 0.0) before training."""
        # Create miner without warehouse (won't be used)
        class DummyWH:
            def query(self, sql):
                return None

        miner = CampusIssueMiner(DummyWH())
        category, confidence = miner.predict_category("Test issue")

        assert category is None
        assert confidence == 0.0

    def test_prediction_after_training(self, full_warehouse):
        """Test that prediction works after training."""
        miner = CampusIssueMiner(full_warehouse)
        miner.train_classifier()

        # Test with a known Wi-Fi related text
        category, confidence = miner.predict_category("WiFi not working in the lab")
        assert category is not None
        assert 0 <= confidence <= 1

    def test_prediction_with_empty_input(self, full_warehouse):
        """Test that prediction handles empty input gracefully."""
        miner = CampusIssueMiner(full_warehouse)
        miner.train_classifier()

        category, confidence = miner.predict_category("")
        assert category is None
        assert confidence == 0.0

    def test_prediction_with_invalid_input(self, full_warehouse):
        """Test that prediction handles invalid input gracefully."""
        miner = CampusIssueMiner(full_warehouse)
        miner.train_classifier()

        category, confidence = miner.predict_category(None)
        assert category is None
        assert confidence == 0.0


class TestKMeansClustering:
    """Tests for K-Means clustering."""

    def test_clustering_on_full_data(self, full_warehouse):
        """Test that clustering works on full dataset."""
        miner = CampusIssueMiner(full_warehouse)
        result = miner.perform_clustering(n_clusters=3)

        assert result is not None
        assert "silhouette_score" in result
        assert "n_clusters" in result
        assert -1 <= result["silhouette_score"] <= 1

    def test_clustering_returns_none_on_insufficient_data(self, empty_warehouse):
        """Test that clustering returns None with insufficient data."""
        miner = CampusIssueMiner(empty_warehouse)
        result = miner.perform_clustering(n_clusters=3)

        assert result is None

    def test_clustering_with_more_clusters_than_samples(self, populated_warehouse):
        """Test that clustering returns None when n_clusters > sample count."""
        miner = CampusIssueMiner(populated_warehouse)
        # populated_warehouse has 50 records, request 100 clusters
        result = miner.perform_clustering(n_clusters=100)

        assert result is None


class TestAprioriAssociationRules:
    """Tests for Apriori association rule mining."""

    def test_apriori_generates_rules(self, full_warehouse):
        """Test that Apriori generates rules on full dataset."""
        miner = CampusIssueMiner(full_warehouse)
        result = miner.mine_association_rules(min_support=0.05, min_confidence=0.3)

        # Result should be a list of dicts or None
        if result is not None:
            assert isinstance(result, list)
            assert len(result) > 0
            # Each rule should have key metrics
            if len(result) > 0:
                first_rule = result[0]
                assert "support" in first_rule or "lift" in first_rule

    def test_apriori_returns_none_on_empty_data(self, empty_warehouse):
        """Test that Apriori returns None on empty warehouse."""
        miner = CampusIssueMiner(empty_warehouse)
        result = miner.mine_association_rules()

        assert result is None

    def test_apriori_with_high_thresholds(self, full_warehouse):
        """Test Apriori with very high support/confidence thresholds."""
        miner = CampusIssueMiner(full_warehouse)
        # Very high thresholds likely to produce no rules
        result = miner.mine_association_rules(min_support=0.99, min_confidence=0.99)

        # Result should be None or empty list (graceful handling)
        assert result is None or len(result) == 0


class TestModelSerialization:
    """Tests for model save/load operations."""

    def test_save_models_after_training(self, full_warehouse, tmp_path):
        """Test that models can be saved after training."""
        miner = CampusIssueMiner(full_warehouse)
        miner.train_classifier()

        # Save to temporary directory
        model_dir = str(tmp_path)
        miner.save_models(model_dir)

        # Check that files exist
        import os
        assert os.path.exists(os.path.join(model_dir, "classifier.pkl"))
        assert os.path.exists(os.path.join(model_dir, "vectorizer.pkl"))

    def test_load_models(self, full_warehouse, tmp_path):
        """Test that models can be loaded after saving."""
        miner1 = CampusIssueMiner(full_warehouse)
        miner1.train_classifier()

        model_dir = str(tmp_path)
        miner1.save_models(model_dir)

        # Create new miner and load
        miner2 = CampusIssueMiner(full_warehouse)
        success = miner2.load_models(model_dir)

        assert success is True
        assert miner2.classifier is not None
        assert miner2.vectorizer is not None

    def test_load_models_from_nonexistent_dir(self, full_warehouse):
        """Test that load_models handles missing directory gracefully."""
        miner = CampusIssueMiner(full_warehouse)
        success = miner.load_models("/nonexistent/path")

        assert success is False
        assert miner.classifier is None


class TestEdgeCases:
    """Edge case tests across all algorithms."""

    def test_all_algorithms_on_populated_warehouse(self, populated_warehouse):
        """Test that all algorithms run without crashing on small dataset."""
        miner = CampusIssueMiner(populated_warehouse)

        # All should complete without exceptions
        cls_result = miner.train_classifier()
        clust_result = miner.perform_clustering(n_clusters=2)
        apriori_result = miner.mine_association_rules(min_support=0.1, min_confidence=0.2)

        # At least some should succeed
        assert cls_result is not None or clust_result is not None

    def test_miner_initialization_without_models(self, full_warehouse):
        """Test that miner initializes correctly without pre-trained models."""
        miner = CampusIssueMiner(full_warehouse)

        assert miner.classifier is None
        assert miner.vectorizer is None
        assert miner.kmeans is None
        assert miner.tfidf_matrix is None
