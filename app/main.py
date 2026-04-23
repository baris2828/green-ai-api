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


app = FastAPI(
    title="Green-AI API",
    description=(
        "Estimate and optimize the carbon footprint of your cloud AI workloads. "
        "Compare regions, get migration savings, and receive actionable recommendations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/regions")
async def list_regions() -> dict[str, list[str]]:
    return {"regions": sorted(REGION_CARBON_INTENSITY.keys())}


@app.get("/instances")
async def list_instances() -> dict[str, list[str]]:
    return {"instances": sorted(INSTANCE_TDP_WATTS.keys())}


@app.post("/co2", response_model=CO2Response)
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


@app.post("/compare", response_model=CompareResponse)
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


@app.post("/optimize", response_model=OptimizeResponse)
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
