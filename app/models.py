from pydantic import BaseModel, Field


class CO2Request(BaseModel):
    region: str = Field(
        ...,
        description="Cloud region identifier, e.g. 'aws-us-east-1'",
        examples=["aws-us-east-1", "gcp-europe-west6"],
    )
    instance_type: str = Field(
        ...,
        description="Instance type, e.g. 't3.medium'",
        examples=["t3.medium", "n1-standard-4"],
    )
    utilization: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average CPU utilization as fraction (0.0 to 1.0)",
        examples=[0.5, 0.75],
    )
    hours: float = Field(
        default=720.0,
        gt=0.0,
        description="Runtime in hours (default: 720 = 1 month)",
    )


class CO2Response(BaseModel):
    region: str
    instance_type: str
    utilization: float
    hours: float
    energy_kwh: float = Field(description="Estimated energy consumption in kWh")
    carbon_g: float = Field(description="Estimated CO2 emissions in grams")
    carbon_kg: float = Field(description="Estimated CO2 emissions in kilograms")


class CompareRequest(BaseModel):
    source_region: str = Field(
        ...,
        description="Current region, e.g. 'aws-us-east-1'",
        examples=["aws-us-east-1"],
    )
    target_region: str = Field(
        ...,
        description="Target green region, e.g. 'gcp-europe-west6'",
        examples=["gcp-europe-west6"],
    )
    instance_type: str = Field(
        ...,
        description="Instance type to compare",
        examples=["m5.xlarge"],
    )
    utilization: float = Field(default=0.5, ge=0.0, le=1.0)
    hours: float = Field(default=720.0, gt=0.0)


class CompareResponse(BaseModel):
    source_region: str
    target_region: str
    source_carbon_kg: float
    target_carbon_kg: float
    savings_kg: float
    savings_percent: float


class Recommendation(BaseModel):
    title: str
    description: str
    estimated_savings_percent: float


class OptimizeRequest(BaseModel):
    region: str = Field(..., examples=["aws-us-east-1"])
    instance_type: str = Field(..., examples=["m5.xlarge"])
    utilization: float = Field(default=0.5, ge=0.0, le=1.0)
    workload_type: str = Field(
        default="general",
        description="Workload type: 'general', 'ml-training', 'batch', 'web-serving'",
    )


class OptimizeResponse(BaseModel):
    current_region: str
    current_carbon_kg: float
    recommendations: list[Recommendation]
    best_region: str
    best_region_carbon_kg: float
