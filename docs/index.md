# EOAP OpenAPI Health Check

EOAP OpenAPI Health Check defines a consistent, machine-readable way for EOAP
services to describe their operational health. It gives service implementers,
platform operators, monitoring systems, and client applications a common
contract instead of requiring each service to invent its own health payload.

The project is based on the
[`application/health+json` Internet-Draft](https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check-06).
That draft defines the representation; this project supplies an OpenAPI 3.1
description and uses the conventional `/health` path as an implementation
choice.

## Purpose

The contract is intended to make health information portable across EOAP
components. A producer can return a predictable payload, while a consumer can
validate and interpret that payload without depending on service-specific
response shapes.

The OpenAPI definition supports two complementary use cases:

- **API integration.** Services in any language can implement the documented
  `GET /health` operation and use the schema to validate responses or generate
  client code.
- **Python integration.** Pydantic models generated from the same definition
  are published to PyPI as `eoap-api-health-check`, allowing Python services to
  construct and validate compatible payloads directly.

The OpenAPI file is therefore the source of truth. Generated Python models and
rendered documentation are delivery formats of the same contract, not separate
definitions to maintain by hand.

## Health representation

Every response contains a required `status`. The supported outcomes are:

| Outcome | Accepted values | Meaning |
| --- | --- | --- |
| Healthy | `pass`, `ok`, `up` | The service is operating normally. |
| Warning | `warn` | The service is available, but one or more observations need attention. |
| Unhealthy | `fail`, `error`, `down` | The service cannot operate normally. |

The aliases make it easier to integrate services that already expose common
framework conventions, including Node Terminus and Spring Boot terminology.

A response may also contain:

- `version`, `releaseId`, and `serviceId` to identify the running service and
  release;
- `description`, `notes`, and `output` to provide human-readable context;
- `links` to related resources; and
- `checks` with observations about dependencies or internal sub-components.

Checks are grouped under keys such as `database:responseTime`. Each key maps to
an array so that a logical component can report observations for one or more
instances. An observation can include a component identifier and type, an
observed value and unit, its own status, a timestamp, affected API endpoints,
diagnostic output, and related links.

```json
{
  "status": "warn",
  "version": "1.0.0",
  "notes": ["Database latency is elevated"],
  "checks": {
    "database:responseTime": [
      {
        "componentType": "datastore",
        "observedValue": 900,
        "observedUnit": "ms",
        "status": "warn",
        "time": "2026-07-22T10:00:00Z"
      }
    ]
  }
}
```

## Using the Python package

Install the generated Pydantic models from PyPI:

```console
pip install eoap-api-health-check
```

Then create or validate a response using the models exported by
`eoap_api_health_check`:

```python
from eoap_api_health_check import ComponentHealth, WarnResponse

health = WarnResponse(
    notes=["Database latency is elevated"],
    checks={
        "database:responseTime": [
            ComponentHealth(
                componentType="datastore",
                observedValue=900,
                observedUnit="ms",
                status="warn",
            )
        ]
    },
)

payload = health.model_dump(by_alias=True, mode="json", exclude_none=True)
```

The models use idiomatic `snake_case` Python attributes and accept the
camel-cased OpenAPI property names as aliases. Use `by_alias=True` when
serializing a response for the API.

## Project artifacts

- [OpenAPI definition](openapi.yaml) — the complete API and schema contract.
- [Rendered OpenAPI reference](openapi.html) — an interactive view generated
  from the definition.
- [Python package](https://pypi.org/project/eoap-api-health-check/) — generated
  Pydantic models for Python applications.
- [Source repository](https://github.com/eoap/api-health-check) — schema,
  generation workflow, and project history.

Changes should begin in `schemas/openapi.yaml` in the source repository. The
Pydantic models and documentation artifacts are regenerated from it before a
new package version is published.
