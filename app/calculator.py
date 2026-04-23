from app.carbon_data import (
    GREEN_REGIONS,
    INSTANCE_TDP_WATTS,
    PUE_BY_PROVIDER,
    REGION_CARBON_INTENSITY,
)
from app.models import Recommendation


def _provider_from_region(region: str) -> str:
    return region.split("-")[0]


def _pue_for_region(region: str) -> float:
    return PUE_BY_PROVIDER.get(_provider_from_region(region), 1.2)


def compute_energy_kwh(
    instance_type: str, utilization: float, hours: float, region: str
) -> float:
    tdp = INSTANCE_TDP_WATTS.get(instance_type, 50.0)
    idle_fraction = 0.3
    effective_watts = tdp * (idle_fraction + (1.0 - idle_fraction) * utilization)
    pue = _pue_for_region(region)
    return effective_watts * pue * hours / 1000.0


def compute_carbon_grams(energy_kwh: float, region: str) -> float:
    intensity = REGION_CARBON_INTENSITY.get(region, 400.0)
    return energy_kwh * intensity


def compute_carbon_kg(energy_kwh: float, region: str) -> float:
    return compute_carbon_grams(energy_kwh, region) / 1000.0


def find_best_green_region(
    instance_type: str, utilization: float, hours: float
) -> tuple[str, float]:
    best_region = GREEN_REGIONS[0]
    best_carbon = float("inf")
    for region in GREEN_REGIONS:
        energy = compute_energy_kwh(instance_type, utilization, hours, region)
        carbon = compute_carbon_kg(energy, region)
        if carbon < best_carbon:
            best_carbon = carbon
            best_region = region
    return best_region, best_carbon


def generate_recommendations(
    region: str,
    instance_type: str,
    utilization: float,
    workload_type: str,
) -> list[Recommendation]:
    recs: list[Recommendation] = []

    intensity = REGION_CARBON_INTENSITY.get(region, 400.0)
    if intensity > 200:
        recs.append(
            Recommendation(
                title="Migrate to a low-carbon region",
                description=(
                    f"Region '{region}' has {intensity} gCO2eq/kWh. "
                    "Consider gcp-europe-west6 (25 gCO2eq/kWh) or "
                    "gcp-northamerica-northeast1 (15 gCO2eq/kWh)."
                ),
                estimated_savings_percent=round(
                    (1.0 - 25.0 / intensity) * 100, 1
                ),
            )
        )

    if utilization < 0.3:
        recs.append(
            Recommendation(
                title="Right-size your instance",
                description=(
                    f"Utilization is only {utilization:.0%}. "
                    "Downsizing the instance type can reduce energy waste by ~40%."
                ),
                estimated_savings_percent=40.0,
            )
        )

    if workload_type == "web-serving":
        recs.append(
            Recommendation(
                title="Use Cloud Run instead of always-on VMs",
                description=(
                    "For web-serving workloads, serverless platforms like Cloud Run "
                    "scale to zero and eliminate standby emissions."
                ),
                estimated_savings_percent=30.0,
            )
        )

    if workload_type == "ml-training":
        recs.append(
            Recommendation(
                title="Use spot/preemptible instances for training",
                description=(
                    "ML training jobs tolerate interruptions. Spot instances "
                    "improve fleet utilization across the datacenter."
                ),
                estimated_savings_percent=15.0,
            )
        )

    if workload_type == "batch":
        recs.append(
            Recommendation(
                title="Schedule batch jobs during low-carbon hours",
                description=(
                    "Shift batch workloads to off-peak hours when the grid's "
                    "renewable share is higher (typically midday or overnight)."
                ),
                estimated_savings_percent=20.0,
            )
        )

    if _provider_from_region(region) != "gcp":
        recs.append(
            Recommendation(
                title="Consider GCP for lower PUE",
                description=(
                    "Google Cloud achieves a PUE of 1.1 vs. industry average ~1.6. "
                    "Lower PUE means less energy overhead for cooling."
                ),
                estimated_savings_percent=8.0,
            )
        )

    return recs
