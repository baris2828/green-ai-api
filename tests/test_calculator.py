import pytest

from app.calculator import (
    compute_carbon_grams,
    compute_carbon_kg,
    compute_energy_kwh,
    find_best_green_region,
    generate_recommendations,
)


class TestComputeEnergyKwh:
    def test_full_utilization(self):
        energy = compute_energy_kwh("t3.medium", 1.0, 720.0, "aws-us-east-1")
        # TDP=20W, idle=0.3, effective=20*(0.3+0.7*1.0)=20W, PUE=1.2
        # 20 * 1.2 * 720 / 1000 = 17.28 kWh
        assert energy == pytest.approx(17.28, rel=1e-3)

    def test_zero_utilization(self):
        energy = compute_energy_kwh("t3.medium", 0.0, 720.0, "aws-us-east-1")
        # effective=20*0.3=6W, PUE=1.2 → 6*1.2*720/1000 = 5.184 kWh
        assert energy == pytest.approx(5.184, rel=1e-3)

    def test_gcp_lower_pue(self):
        energy_aws = compute_energy_kwh("t3.medium", 0.5, 720.0, "aws-us-east-1")
        energy_gcp = compute_energy_kwh("t3.medium", 0.5, 720.0, "gcp-europe-west6")
        assert energy_gcp < energy_aws

    def test_unknown_instance_uses_default_tdp(self):
        energy = compute_energy_kwh("unknown-instance", 0.5, 100.0, "aws-us-east-1")
        # default TDP=50W, utilization=0.5, idle=0.3
        # effective = 50*(0.3+0.7*0.5) = 50*0.65 = 32.5W, PUE=1.2
        # 32.5 * 1.2 * 100 / 1000 = 3.9
        assert energy == pytest.approx(3.9, rel=1e-3)


class TestComputeCarbon:
    def test_carbon_grams_known_region(self):
        carbon = compute_carbon_grams(10.0, "aws-us-east-1")
        # 10 kWh * 379 gCO2/kWh = 3790g
        assert carbon == pytest.approx(3790.0, rel=1e-3)

    def test_carbon_kg_conversion(self):
        carbon_g = compute_carbon_grams(10.0, "aws-us-east-1")
        carbon_kg = compute_carbon_kg(10.0, "aws-us-east-1")
        assert carbon_kg == pytest.approx(carbon_g / 1000.0, rel=1e-6)

    def test_green_region_low_carbon(self):
        carbon_dirty = compute_carbon_kg(10.0, "aws-us-east-1")
        carbon_green = compute_carbon_kg(10.0, "gcp-europe-west6")
        assert carbon_green < carbon_dirty
        assert carbon_green < 1.0  # 10kWh * 25g/kWh = 250g = 0.25kg


class TestFindBestGreenRegion:
    def test_returns_lowest_carbon_region(self):
        best_region, best_carbon = find_best_green_region("m5.xlarge", 0.5, 720.0)
        assert best_region in (
            "gcp-northamerica-northeast1",
            "gcp-europe-west6",
            "azure-swedencentral",
        )
        assert best_carbon > 0


class TestGenerateRecommendations:
    def test_dirty_region_suggests_migration(self):
        recs = generate_recommendations("aws-us-east-1", "m5.xlarge", 0.5, "general")
        titles = [r.title for r in recs]
        assert "Migrate to a low-carbon region" in titles

    def test_low_utilization_suggests_rightsizing(self):
        recs = generate_recommendations("aws-us-east-1", "m5.xlarge", 0.1, "general")
        titles = [r.title for r in recs]
        assert "Right-size your instance" in titles

    def test_web_serving_suggests_cloud_run(self):
        recs = generate_recommendations(
            "aws-us-east-1", "m5.xlarge", 0.5, "web-serving"
        )
        titles = [r.title for r in recs]
        assert "Use Cloud Run instead of always-on VMs" in titles

    def test_ml_training_suggests_spot(self):
        recs = generate_recommendations(
            "gcp-europe-west6", "a2-highgpu-1g", 0.8, "ml-training"
        )
        titles = [r.title for r in recs]
        assert "Use spot/preemptible instances for training" in titles
