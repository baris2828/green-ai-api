from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCO2Endpoint:
    def test_valid_request(self):
        resp = client.post(
            "/co2",
            json={
                "region": "aws-us-east-1",
                "instance_type": "t3.medium",
                "utilization": 0.5,
                "hours": 720,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["carbon_kg"] > 0
        assert data["energy_kwh"] > 0

    def test_unknown_region(self):
        resp = client.post(
            "/co2",
            json={
                "region": "unknown-region",
                "instance_type": "t3.medium",
                "utilization": 0.5,
            },
        )
        assert resp.status_code == 400

    def test_invalid_utilization(self):
        resp = client.post(
            "/co2",
            json={
                "region": "aws-us-east-1",
                "instance_type": "t3.medium",
                "utilization": 1.5,
            },
        )
        assert resp.status_code == 422


class TestCompareEndpoint:
    def test_savings_positive_for_green_target(self):
        resp = client.post(
            "/compare",
            json={
                "source_region": "aws-us-east-1",
                "target_region": "gcp-europe-west6",
                "instance_type": "m5.xlarge",
                "utilization": 0.5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["savings_kg"] > 0
        assert data["savings_percent"] > 0


class TestOptimizeEndpoint:
    def test_returns_recommendations(self):
        resp = client.post(
            "/optimize",
            json={
                "region": "aws-us-east-1",
                "instance_type": "m5.xlarge",
                "utilization": 0.5,
                "workload_type": "web-serving",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recommendations"]) > 0
        assert data["best_region"] != ""
