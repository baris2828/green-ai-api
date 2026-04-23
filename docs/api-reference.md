# API Reference

## Endpoints

### `GET /health`
Health check endpoint.

**Response:** `{"status": "ok"}`

### `GET /regions`
List all supported cloud regions.

### `GET /instances`
List all supported instance types.

### `POST /co2`
Estimate CO2 emissions for a given cloud workload.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| region | string | yes | Cloud region (e.g. `aws-us-east-1`) |
| instance_type | string | yes | Instance type (e.g. `t3.medium`) |
| utilization | float | yes | CPU utilization 0.0–1.0 |
| hours | float | no | Runtime hours (default: 720) |

### `POST /compare`
Compare CO2 emissions between two regions.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_region | string | yes | Current region |
| target_region | string | yes | Target region |
| instance_type | string | yes | Instance type |
| utilization | float | no | CPU utilization (default: 0.5) |
| hours | float | no | Runtime hours (default: 720) |

### `POST /optimize`
Get optimization recommendations for reducing carbon footprint.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| region | string | yes | Current region |
| instance_type | string | yes | Instance type |
| utilization | float | no | CPU utilization (default: 0.5) |
| workload_type | string | no | `general`, `ml-training`, `batch`, `web-serving` |
