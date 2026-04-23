from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException

from app.calculator import (
    compute_carbon_grams,
    compute_carbon_kg,
    compute_energy_kwh,
    find_best_green_region,
    generate_recommendations,
)
from app.carbon_data import INSTANCE_TDP_WATTS, REGION_CARBON_INTENSITY
from app.logging_config import setup_logging
from app.models import (
    CO2Request,
    CO2Response,
    CompareRequest,
    CompareResponse,
    OptimizeRequest,
    OptimizeResponse,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("green_ai_api.startup", regions=len(REGION_CARBON_INTENSITY))
    yield
    logger.info("green_ai_api.shutdown")


OPENAPI_TAGS = [
    {
        "name": "Carbon Estimation",
        "description": (
            "Estimate CO2 emissions for cloud workloads based on "
            "region, instance type, and utilization."
        ),
    },
    {
        "name": "Region Comparison",
        "description": "Compare carbon footprints between regions and quantify migration savings.",
    },
    {
        "name": "Optimization",
        "description": "Get actionable recommendations to reduce your cloud carbon footprint.",
    },
    {
        "name": "Reference Data",
        "description": "List supported regions and instance types.",
    },
    {
        "name": "System",
        "description": "Health checks and operational endpoints.",
    },
]

app = FastAPI(
    title="Green-AI API",
    summary="Carbon footprint estimation and optimization for cloud AI workloads",
    description=(
        "## Overview\n\n"
        "The Green-AI API helps engineering teams **measure, compare, and reduce** "
        "the carbon footprint of their cloud infrastructure.\n\n"
        "### How it works\n\n"
        "1. **Estimate** — Calculate CO2 emissions for a workload given region, "
        "instance type, and utilization\n"
        "2. **Compare** — Quantify savings from migrating to a greener region "
        "(e.g., `aws-us-east-1` → `gcp-europe-west6` saves ~94%)\n"
        "3. **Optimize** — Receive tailored recommendations: region migration, "
        "right-sizing, serverless, spot instances, batch scheduling\n\n"
        "### Data sources\n\n"
        "- Grid carbon intensity: [Electricity Maps](https://app.electricitymaps.com)\n"
        "- PUE values: Google (1.1), AWS (1.2), Azure (1.18)\n"
        "- Instance TDP: published spec sheets"
    ),
    version="1.0.0",
    contact={"name": "Green-AI API", "url": "https://github.com/ipbaro55/green-ai-api"},
    license_info={"name": "MIT", "identifier": "MIT"},
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description=(
        "Returns HTTP 200 if the service is running. "
        "Use this for load balancer and Kubernetes liveness probes."
    ),
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/regions",
    tags=["Reference Data"],
    summary="List supported cloud regions",
    description=(
        "Returns all cloud regions (AWS, GCP, Azure) for which carbon intensity "
        "data is available. Use these identifiers in the "
        "`/co2`, `/compare`, and `/optimize` endpoints."
    ),
)
async def list_regions() -> dict[str, list[str]]:
    return {"regions": sorted(REGION_CARBON_INTENSITY.keys())}


@app.get(
    "/instances",
    tags=["Reference Data"],
    summary="List supported instance types",
    description=(
        "Returns all instance types for which TDP (thermal design power) "
        "data is available. Use these identifiers in the "
        "`/co2`, `/compare`, and `/optimize` endpoints."
    ),
)
async def list_instances() -> dict[str, list[str]]:
    return {"instances": sorted(INSTANCE_TDP_WATTS.keys())}


@app.post(
    "/co2",
    response_model=CO2Response,
    tags=["Carbon Estimation"],
    summary="Estimate CO2 emissions for a workload",
    description=(
        "Calculate the estimated energy consumption (kWh) and CO2 emissions (grams/kg) "
        "for a given cloud instance running in a specific region.\n\n"
        "The calculation accounts for:\n"
        "- **Instance TDP** — base power draw of the instance type\n"
        "- **Utilization scaling** — 30% idle power + linear scaling to full TDP\n"
        "- **PUE (Power Usage Effectiveness)** — datacenter cooling overhead per provider\n"
        "- **Grid carbon intensity** — gCO2eq/kWh for the region's electricity grid"
    ),
    responses={
        400: {"description": "Unknown region or instance type"},
    },
)
async def estimate_co2(req: CO2Request) -> CO2Response:
    logger.info(
        "co2.estimate",
        region=req.region,
        instance_type=req.instance_type,
        utilization=req.utilization,
    )

    if req.region not in REGION_CARBON_INTENSITY:
        raise HTTPException(status_code=400, detail=f"Unknown region: {req.region}")
    if req.instance_type not in INSTANCE_TDP_WATTS:
        raise HTTPException(
            status_code=400, detail=f"Unknown instance type: {req.instance_type}"
        )

    energy = compute_energy_kwh(req.instance_type, req.utilization, req.hours, req.region)
    carbon_g = compute_carbon_grams(energy, req.region)
    carbon_kg = compute_carbon_kg(energy, req.region)

    return CO2Response(
        region=req.region,
        instance_type=req.instance_type,
        utilization=req.utilization,
        hours=req.hours,
        energy_kwh=round(energy, 4),
        carbon_g=round(carbon_g, 2),
        carbon_kg=round(carbon_kg, 4),
    )


@app.post(
    "/compare",
    response_model=CompareResponse,
    tags=["Region Comparison"],
    summary="Compare CO2 between two regions",
    description=(
        "Quantify the carbon savings from migrating an identical workload from a "
        "high-carbon source region to a lower-carbon target region.\n\n"
        "Returns absolute savings in kg and relative savings as a percentage. "
        "Tip: use `GET /regions` to discover available region identifiers."
    ),
    responses={
        400: {"description": "Unknown region or instance type"},
    },
)
async def compare_regions(req: CompareRequest) -> CompareResponse:
    logger.info(
        "compare.regions",
        source=req.source_region,
        target=req.target_region,
    )

    for region in (req.source_region, req.target_region):
        if region not in REGION_CARBON_INTENSITY:
            raise HTTPException(status_code=400, detail=f"Unknown region: {region}")
    if req.instance_type not in INSTANCE_TDP_WATTS:
        raise HTTPException(
            status_code=400, detail=f"Unknown instance type: {req.instance_type}"
        )

    src_energy = compute_energy_kwh(
        req.instance_type, req.utilization, req.hours, req.source_region
    )
    tgt_energy = compute_energy_kwh(
        req.instance_type, req.utilization, req.hours, req.target_region
    )

    src_carbon = compute_carbon_kg(src_energy, req.source_region)
    tgt_carbon = compute_carbon_kg(tgt_energy, req.target_region)

    savings_kg = src_carbon - tgt_carbon
    savings_pct = (savings_kg / src_carbon * 100) if src_carbon > 0 else 0.0

    return CompareResponse(
        source_region=req.source_region,
        target_region=req.target_region,
        source_carbon_kg=round(src_carbon, 4),
        target_carbon_kg=round(tgt_carbon, 4),
        savings_kg=round(savings_kg, 4),
        savings_percent=round(savings_pct, 2),
    )


@app.post(
    "/optimize",
    response_model=OptimizeResponse,
    tags=["Optimization"],
    summary="Get optimization recommendations",
    description=(
        "Analyze a workload and return tailored recommendations to reduce its carbon footprint.\n\n"
        "Recommendations vary by context:\n"
        "- **High-carbon region** → suggests migration to green regions\n"
        "- **Low utilization (<30%)** → suggests right-sizing the instance\n"
        "- **web-serving** workloads → suggests Cloud Run (scale-to-zero)\n"
        "- **ml-training** workloads → suggests spot/preemptible instances\n"
        "- **batch** workloads → suggests scheduling during low-carbon grid hours\n"
        "- **Non-GCP providers** → highlights GCP's lower PUE (1.1 vs. industry ~1.6)"
    ),
    responses={
        400: {"description": "Unknown region or instance type"},
    },
)
async def optimize(req: OptimizeRequest) -> OptimizeResponse:
    logger.info("optimize.request", region=req.region, workload=req.workload_type)

    if req.region not in REGION_CARBON_INTENSITY:
        raise HTTPException(status_code=400, detail=f"Unknown region: {req.region}")
    if req.instance_type not in INSTANCE_TDP_WATTS:
        raise HTTPException(
            status_code=400, detail=f"Unknown instance type: {req.instance_type}"
        )

    energy = compute_energy_kwh(req.instance_type, req.utilization, 720.0, req.region)
    current_carbon = compute_carbon_kg(energy, req.region)

    recommendations = generate_recommendations(
        req.region, req.instance_type, req.utilization, req.workload_type
    )

    best_region, best_carbon = find_best_green_region(
        req.instance_type, req.utilization, 720.0
    )

    return OptimizeResponse(
        current_region=req.region,
        current_carbon_kg=round(current_carbon, 4),
        recommendations=recommendations,
        best_region=best_region,
        best_region_carbon_kg=round(best_carbon, 4),
    )
