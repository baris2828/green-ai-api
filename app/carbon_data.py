"""Carbon intensity data for cloud regions (gCO2eq/kWh)."""

REGION_CARBON_INTENSITY: dict[str, float] = {
    # AWS
    "aws-us-east-1": 379.0,
    "aws-us-east-2": 410.0,
    "aws-us-west-1": 210.0,
    "aws-us-west-2": 100.0,
    "aws-eu-west-1": 300.0,
    "aws-eu-central-1": 338.0,
    "aws-ap-southeast-1": 493.0,
    "aws-ap-northeast-1": 463.0,
    # GCP
    "gcp-us-central1": 394.0,
    "gcp-us-east1": 390.0,
    "gcp-us-west1": 40.0,
    "gcp-europe-west1": 120.0,
    "gcp-europe-west4": 402.0,
    "gcp-europe-west6": 25.0,
    "gcp-asia-east1": 509.0,
    "gcp-northamerica-northeast1": 15.0,
    # Azure
    "azure-eastus": 379.0,
    "azure-westus2": 100.0,
    "azure-westeurope": 300.0,
    "azure-northeurope": 170.0,
    "azure-swedencentral": 15.0,
}

INSTANCE_TDP_WATTS: dict[str, float] = {
    "t3.micro": 10.0,
    "t3.medium": 20.0,
    "t3.large": 35.0,
    "m5.large": 55.0,
    "m5.xlarge": 100.0,
    "c5.large": 50.0,
    "c5.xlarge": 95.0,
    "n1-standard-1": 38.0,
    "n1-standard-4": 95.0,
    "e2-medium": 18.0,
    "e2-standard-4": 70.0,
    "a2-highgpu-1g": 300.0,
    "p3.2xlarge": 350.0,
    "Standard_B1s": 10.0,
    "Standard_D2s_v3": 45.0,
    "Standard_D4s_v3": 90.0,
}

PUE_BY_PROVIDER: dict[str, float] = {
    "aws": 1.2,
    "gcp": 1.1,
    "azure": 1.18,
}

GREEN_REGIONS: list[str] = [
    "gcp-europe-west6",
    "gcp-northamerica-northeast1",
    "gcp-us-west1",
    "azure-swedencentral",
    "aws-us-west-2",
]
