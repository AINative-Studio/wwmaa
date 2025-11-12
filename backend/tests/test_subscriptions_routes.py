"""
Tests for Subscriptions Routes

Tests the public subscription tiers endpoint that returns membership
pricing and benefits information.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.models.schemas import SubscriptionTier

client = TestClient(app)


class TestSubscriptionsRoutes:
    """Test suite for subscriptions routes"""

    def test_get_subscription_tiers_success(self):
        """Test successful retrieval of all subscription tiers"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "tiers" in data
        assert "total" in data
        assert isinstance(data["tiers"], list)
        assert data["total"] == len(list(SubscriptionTier))

        # Verify all tiers are present
        tier_ids = [tier["id"] for tier in data["tiers"]]
        assert "free" in tier_ids
        assert "basic" in tier_ids
        assert "premium" in tier_ids
        assert "lifetime" in tier_ids

    def test_subscription_tier_structure(self):
        """Test that each tier has the correct structure"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        for tier in data["tiers"]:
            # Verify required fields
            assert "id" in tier
            assert "code" in tier
            assert "name" in tier
            assert "price_usd" in tier
            assert "billing_interval" in tier
            assert "benefits" in tier
            assert "features" in tier
            assert "is_popular" in tier

            # Verify field types
            assert isinstance(tier["id"], str)
            assert isinstance(tier["code"], str)
            assert isinstance(tier["name"], str)
            assert isinstance(tier["price_usd"], (int, float))
            assert isinstance(tier["billing_interval"], str)
            assert isinstance(tier["benefits"], list)
            assert isinstance(tier["features"], dict)
            assert isinstance(tier["is_popular"], bool)

    def test_subscription_tier_pricing(self):
        """Test that pricing matches expected values"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        tier_pricing = {tier["id"]: tier["price_usd"] for tier in data["tiers"]}

        # Verify pricing matches TIER_PRICING constant
        assert tier_pricing["free"] == 0.0
        assert tier_pricing["basic"] == 29.0
        assert tier_pricing["premium"] == 79.0
        assert tier_pricing["lifetime"] == 149.0

    def test_subscription_tier_billing_intervals(self):
        """Test that billing intervals are correct"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        tier_intervals = {tier["id"]: tier["billing_interval"] for tier in data["tiers"]}

        assert tier_intervals["free"] == "free"
        assert tier_intervals["basic"] == "year"
        assert tier_intervals["premium"] == "year"
        assert tier_intervals["lifetime"] == "lifetime"

    def test_premium_tier_is_popular(self):
        """Test that Premium tier is marked as popular"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        for tier in data["tiers"]:
            if tier["id"] == "premium":
                assert tier["is_popular"] is True
            else:
                assert tier["is_popular"] is False

    def test_get_subscription_tier_by_id_success(self):
        """Test successful retrieval of a single subscription tier"""
        response = client.get("/api/subscriptions/basic")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "basic"
        assert data["code"] == "BASIC"
        assert data["name"] == "Basic Membership"
        assert data["price_usd"] == 29.0
        assert data["billing_interval"] == "year"
        assert isinstance(data["benefits"], list)
        assert len(data["benefits"]) > 0

    def test_get_subscription_tier_by_id_case_insensitive(self):
        """Test that tier ID is case-insensitive"""
        # Test uppercase
        response = client.get("/api/subscriptions/PREMIUM")
        assert response.status_code == 200
        assert response.json()["id"] == "premium"

        # Test mixed case
        response = client.get("/api/subscriptions/LiFeTiMe")
        assert response.status_code == 200
        assert response.json()["id"] == "lifetime"

    def test_get_subscription_tier_invalid_id(self):
        """Test error handling for invalid tier ID"""
        response = client.get("/api/subscriptions/invalid-tier")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid tier ID" in data["detail"]

    def test_tier_benefits_not_empty(self):
        """Test that all tiers have benefits defined"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        for tier in data["tiers"]:
            assert len(tier["benefits"]) > 0, f"{tier['id']} tier has no benefits"

    def test_tier_features_not_empty(self):
        """Test that all tiers have features defined"""
        response = client.get("/api/subscriptions")

        assert response.status_code == 200
        data = response.json()

        for tier in data["tiers"]:
            assert len(tier["features"]) > 0, f"{tier['id']} tier has no features"

    def test_basic_tier_benefits(self):
        """Test that Basic tier has expected benefits"""
        response = client.get("/api/subscriptions/basic")

        assert response.status_code == 200
        data = response.json()

        # Check for key benefits
        benefits = data["benefits"]
        assert any("training video" in b.lower() for b in benefits)
        assert any("member directory" in b.lower() for b in benefits)
        assert any("10%" in b for b in benefits)

    def test_premium_tier_benefits(self):
        """Test that Premium tier has expected benefits"""
        response = client.get("/api/subscriptions/premium")

        assert response.status_code == 200
        data = response.json()

        # Check for key benefits
        benefits = data["benefits"]
        assert any("unlimited" in b.lower() for b in benefits)
        assert any("20%" in b for b in benefits)
        assert any("priority" in b.lower() and "support" in b.lower() for b in benefits)
        assert any("exclusive" in b.lower() for b in benefits)

    def test_lifetime_tier_benefits(self):
        """Test that Lifetime tier has expected benefits"""
        response = client.get("/api/subscriptions/lifetime")

        assert response.status_code == 200
        data = response.json()

        # Check for key benefits
        benefits = data["benefits"]
        assert any("lifetime" in b.lower() for b in benefits)
        assert any("25%" in b for b in benefits)
        assert any("founding member" in b.lower() for b in benefits)
        assert any("instructor" in b.lower() for b in benefits)

    def test_free_tier_no_cost(self):
        """Test that Free tier has zero cost"""
        response = client.get("/api/subscriptions/free")

        assert response.status_code == 200
        data = response.json()

        assert data["price_usd"] == 0.0
        assert data["billing_interval"] == "free"

    def test_health_check(self):
        """Test subscriptions service health check"""
        response = client.get("/api/subscriptions/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "subscriptions"
        assert "tiers_available" in data
        assert data["tiers_available"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
