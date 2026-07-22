# EOAP OpenAPI Health Check

[![PyPI - Version](https://img.shields.io/pypi/v/eoap-api-health-check.svg)](https://pypi.org/project/eoap-api-health-check)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/eoap-api-health-check.svg)](https://pypi.org/project/eoap-api-health-check)

EOAP OpenAPI Health Check provides a shared contract for reporting the health of
EOAP services and their dependencies. The contract follows the
[`application/health+json` Internet-Draft](https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check-06)
and exposes it as an OpenAPI 3.1 definition for a conventional `GET /health`
endpoint.

The OpenAPI definition is the source of truth. It is used to generate:

- Pydantic models, published on PyPI as `eoap-api-health-check`;
- a rendered OpenAPI reference for the project documentation; and
- a reusable API contract for services and tooling in any language.

## What the contract describes

A health response has one of three outcomes:

- `pass` (including the compatible aliases `ok` and `up`) for a healthy
  service;
- `warn` for a service that remains available but has concerns; or
- `fail` (including `error` and `down`) for an unhealthy service.

Responses can include service metadata, diagnostic notes, links, and checks
grouped by dependency or sub-component. Each check can report an observed
value, its unit, the observation time, affected endpoints, and diagnostic
output.

See the [project documentation](https://eoap.github.io/api-health-check/) for
the design and usage overview, or inspect the
[OpenAPI source](schemas/openapi.yaml) for the complete contract.

## Install the Python models

```console
pip install eoap-api-health-check
```

The generated models can be used to construct and validate health payloads:

```python
from eoap_api_health_check import ComponentHealth, HealthyResponse, HealthyStatus

health = HealthyResponse(
    status=HealthyStatus.PASS,
    version="1.0.0",
    checks={
        "database:responseTime": [
            ComponentHealth(
                componentType="datastore",
                observedValue=42,
                observedUnit="ms",
                status=HealthyStatus.PASS,
            )
        ]
    },
)

payload = health.model_dump(by_alias=True, mode="json", exclude_none=True)
```

Property names in Python use `snake_case`; passing aliases such as
`componentType` is also supported. Serializing with `by_alias=True` produces
the camel-cased names defined by the wire format.

## Development

Do not edit `src/eoap_api_health_check/__init__.py` directly: it is regenerated
from `schemas/openapi.yaml`.

With [Task](https://taskfile.dev/) installed, run the complete generation and
validation workflow with:

```console
task
```

Useful focused tasks are:

```console
task process_schema         # regenerate the Pydantic models
task generate_openapi_docs  # refresh the documentation artifacts
task serve_docs             # build and serve the documentation locally
```

## License

This project is licensed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
