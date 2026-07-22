# Copyright 2026 EOAP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from eoap_api_health_check import (
    ComponentHealth,
    HealthyResponse,
    HealthyStatus,
    UnhealthyResponse,
    UnhealthyStatus,
    WarnResponse,
)


class StatusResponseTests(unittest.TestCase):
    def test_healthy_response_accepts_all_supported_statuses(self) -> None:
        for value in ("pass", "ok", "up"):
            with self.subTest(status=value):
                response = HealthyResponse(status=HealthyStatus(value))

                self.assertEqual(response.status, HealthyStatus(value))

    def test_unhealthy_response_accepts_all_supported_statuses(self) -> None:
        for value in ("fail", "error", "down"):
            with self.subTest(status=value):
                response = UnhealthyResponse(status=UnhealthyStatus(value))

                self.assertEqual(response.status, UnhealthyStatus(value))

    def test_healthy_response_defaults_to_up(self) -> None:
        response = HealthyResponse()

        self.assertEqual(response.status, HealthyStatus.UP)
        self.assertEqual(response.model_dump(mode="json")["status"], "up")

    def test_unhealthy_response_defaults_to_fail(self) -> None:
        response = UnhealthyResponse()

        self.assertEqual(response.status, UnhealthyStatus.FAIL)
        self.assertEqual(response.model_dump(mode="json")["status"], "fail")

    def test_response_rejects_a_status_from_another_outcome(self) -> None:
        invalid_statuses = (
            (HealthyResponse, "fail"),
            (UnhealthyResponse, "pass"),
            (WarnResponse, "up"),
        )

        for response_type, status in invalid_statuses:
            with self.subTest(response_type=response_type.__name__, status=status):
                with self.assertRaises(ValidationError):
                    response_type(status=status)

    def test_warn_response_defaults_to_warn(self) -> None:
        response = WarnResponse()

        self.assertEqual(response.status, "warn")


class HealthPayloadTests(unittest.TestCase):
    def test_openapi_aliases_are_accepted_and_used_for_serialization(self) -> None:
        response = HealthyResponse(
            status="pass",
            releaseId="2026.07.22",
            serviceId="catalogue-api",
            checks={
                "database:responseTime": [
                    ComponentHealth(
                        componentId="primary",
                        componentType="datastore",
                        observedValue=42,
                        observedUnit="ms",
                        affectedEndpoints=["/products/{productId}"],
                        status="pass",
                    )
                ]
            },
        )

        payload = response.model_dump(by_alias=True, mode="json", exclude_none=True)

        self.assertEqual(payload["releaseId"], "2026.07.22")
        self.assertEqual(payload["serviceId"], "catalogue-api")
        observation = payload["checks"]["database:responseTime"][0]
        self.assertEqual(observation["componentId"], "primary")
        self.assertEqual(observation["componentType"], "datastore")
        self.assertEqual(observation["observedValue"], 42)
        self.assertEqual(observation["observedUnit"], "ms")
        self.assertEqual(observation["affectedEndpoints"], ["/products/{productId}"])
        self.assertEqual(observation["status"], "pass")

    def test_python_field_names_are_accepted(self) -> None:
        observation = ComponentHealth(
            component_id="database-1",
            component_type="datastore",
            observed_value=18.5,
            observed_unit="ms",
        )

        self.assertEqual(observation.component_id, "database-1")
        self.assertEqual(observation.component_type, "datastore")
        self.assertEqual(observation.observed_value, 18.5)
        self.assertEqual(observation.observed_unit, "ms")

    def test_component_metadata_is_parsed_and_serialized(self) -> None:
        observed_at = datetime(2026, 7, 22, 10, 30, tzinfo=timezone.utc)
        observation = ComponentHealth(
            status="warn",
            time=observed_at,
            output="Response time is above the preferred threshold",
            links={"about": "https://api.example.com/about/database"},
        )

        payload = observation.model_dump(mode="json", exclude_none=True)

        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["time"], "2026-07-22T10:30:00Z")
        self.assertEqual(
            payload["output"], "Response time is above the preferred threshold"
        )
        self.assertEqual(
            payload["links"]["about"], "https://api.example.com/about/database"
        )

    def test_naive_component_timestamp_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ComponentHealth(time="2026-07-22T10:30:00")

    def test_invalid_link_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ComponentHealth(links={"about": "not a URI"})

    def test_empty_checks_mapping_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            HealthyResponse(status="pass", checks={})

    def test_extension_fields_are_preserved(self) -> None:
        observation = ComponentHealth(
            componentType="datastore",
            status="warn",
            retryAfterSeconds=30,
        )
        response = WarnResponse(region="eu-west", checks={"database": [observation]})

        payload = response.model_dump(by_alias=True, mode="json", exclude_none=True)

        self.assertEqual(payload["region"], "eu-west")
        self.assertEqual(payload["checks"]["database"][0]["retryAfterSeconds"], 30)


if __name__ == "__main__":
    unittest.main()
