from enum import Enum

from pydantic import BaseModel, Field


class WorkloadType(str, Enum):
    GENERAL = "general"
    ML_TRAINING = "ml-training"
    BATCH = "batch"
    WEB_SERVING = "web-serving"


class CO2Request(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "region": "aws-us-east-1",
                    "instance_type": "m5.xlarge",
                    "utilization": 0.6,
                    "hours": 720,
                }
            ]
        }
    }

    region: str = Field(
        ...,
        description="Cloud region identifier (provider prefix + region name)",
        examples=["aws-us-east-1", "gcp-europe-west6", "azure-swedencentral"],
    )
    instance_type: str = Field(
        ...,
        description="Cloud instance type — determines base TDP (thermal design power) in watts",
        examples=["t3.medium", "n1-standard-4", "a2-highgpu-1g"],
    )
    utilization: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average CPU utilization as a fraction: 0.0 (idle) to 1.0 (fully loaded)",
        examples=[0.5, 0.75],
    )
    hours: float = Field(
        default=720.0,
        gt=0.0,
        description="Total runtime in hours. Default 720 = ~1 month of continuous operation",
    )


class CO2Response(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "region": "aws-us-east-1",
                    "instance_type": "m5.xlarge",
                    "utilization": 0.6,
                    "hours": 720.0,
                    "energy_kwh": 55.987,
                    "carbon_g": 21219.07,
                    "carbon_kg": 21.2191,
                }
            ]
        }
    }

    region: str = Field(description="The cloud region used for the estimate")
    instance_type: str = Field(description="The instance type used for the estimate")
    utilization: float = Field(description="The CPU utilization fraction used")
    hours: float = Field(description="Runtime hours used for the calculation")
    energy_kwh: float = Field(description="Estimated energy consumption in kilowatt-hours")
    carbon_g: float = Field(description="Estimated CO2-equivalent emissions in grams")
    carbon_kg: float = Field(description="Estimated CO2-equivalent emissions in kilograms")


class CompareRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_region": "aws-us-east-1",
                    "target_region": "gcp-europe-west6",
                    "instance_type": "m5.xlarge",
                    "utilization": 0.5,
                    "hours": 720,
                }
            ]
        }
    }

    source_region: str = Field(
        ...,
        description="Current (high-carbon) region you want to migrate away from",
        examples=["aws-us-east-1", "gcp-asia-east1"],
    )
    target_region: str = Field(
        ...,
        description="Target (low-carbon) region to migrate to",
        examples=["gcp-europe-west6", "gcp-northamerica-northeast1"],
    )
    instance_type: str = Field(
        ...,
        description="Instance type — kept constant for a fair comparison",
        examples=["m5.xlarge"],
    )
    utilization: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Average CPU utilization as a fraction (0.0 to 1.0)",
    )
    hours: float = Field(
        default=720.0,
        gt=0.0,
        description="Runtime in hours for the comparison period",
    )


class CompareResponse(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_region": "aws-us-east-1",
                    "target_region": "gcp-europe-west6",
                    "source_carbon_kg": 18.7034,
                    "target_carbon_kg": 1.1344,
                    "savings_kg": 17.569,
                    "savings_percent": 93.94,
                }
            ]
        }
    }

    source_region: str = Field(description="The source region compared")
    target_region: str = Field(description="The target region compared")
    source_carbon_kg: float = Field(description="CO2 emissions in kg for the source region")
    target_carbon_kg: float = Field(description="CO2 emissions in kg for the target region")
    savings_kg: float = Field(description="Absolute CO2 savings in kg (source − target)")
    savings_percent: float = Field(description="Relative CO2 savings as a percentage")


class Recommendation(BaseModel):
    title: str = Field(description="Short actionable title for the recommendation")
    description: str = Field(description="Detailed explanation with concrete numbers")
    estimated_savings_percent: float = Field(
        description="Estimated carbon reduction in percent if applied"
    )


class OptimizeRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "region": "aws-us-east-1",
                    "instance_type": "m5.xlarge",
                    "utilization": 0.2,
                    "workload_type": "web-serving",
                }
            ]
        }
    }

    region: str = Field(
        ...,
        description="Current cloud region to analyze for optimization potential",
        examples=["aws-us-east-1"],
    )
    instance_type: str = Field(
        ...,
        description="Current instance type to analyze",
        examples=["m5.xlarge", "a2-highgpu-1g"],
    )
    utilization: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Average CPU utilization — low values trigger right-sizing recommendations",
    )
    workload_type: WorkloadType = Field(
        default=WorkloadType.GENERAL,
        description="Workload category — determines which optimization strategies apply",
    )


class OptimizeResponse(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_region": "aws-us-east-1",
                    "current_carbon_kg": 14.9324,
                    "recommendations": [
                        {
                            "title": "Migrate to a low-carbon region",
                            "description": "Region 'aws-us-east-1' has 379.0 gCO2eq/kWh.",
                            "estimated_savings_percent": 93.4,
                        }
                    ],
                    "best_region": "gcp-northamerica-northeast1",
                    "best_region_carbon_kg": 0.5703,
                }
            ]
        }
    }

    current_region: str = Field(description="The region that was analyzed")
    current_carbon_kg: float = Field(
        description="Estimated monthly CO2 emissions for the current setup in kg"
    )
    recommendations: list[Recommendation] = Field(
        description="Ordered list of actionable recommendations to reduce emissions"
    )
    best_region: str = Field(description="Lowest-carbon region from the green-region candidates")
    best_region_carbon_kg: float = Field(
        description="Estimated monthly CO2 in kg if migrated to the best green region"
    )
