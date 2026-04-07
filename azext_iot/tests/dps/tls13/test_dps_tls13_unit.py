# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest.mock import MagicMock
from azext_iot.common.shared import HostnameType
from azext_iot.operations.dps import _transform_enrollment_hub_hostnames, _transform_registration_hub_hostname


class TestTransformEnrollmentHubHostnames:
    """Tests for _transform_enrollment_hub_hostnames — post-processing DPS enrollment results."""

    def test_dict_classic_noop(self):
        result = {"iotHubs": ["hub1.azure-devices.net"]}
        transformed = _transform_enrollment_hub_hostnames(result, HostnameType.CLASSIC.value)
        assert result["iotHubs"] == ["hub1.azure-devices.net"]
        assert transformed is result

    def test_dict_classic_strips_device_prefix(self):
        result = {"iotHubs": ["hub1.device.azure-devices.net"]}
        _transform_enrollment_hub_hostnames(result, HostnameType.CLASSIC.value)
        assert result["iotHubs"] == ["hub1.azure-devices.net"]

    def test_dict_classic_strips_service_prefix(self):
        result = {"iotHubs": ["hub1.service.azure-devices.net"]}
        _transform_enrollment_hub_hostnames(result, HostnameType.CLASSIC.value)
        assert result["iotHubs"] == ["hub1.azure-devices.net"]

    def test_dict_to_device(self):
        result = {"iotHubs": ["hub1.azure-devices.net", "hub2.azure-devices.net"]}
        _transform_enrollment_hub_hostnames(result, HostnameType.DEVICE.value)
        assert result["iotHubs"] == [
            "hub1.device.azure-devices.net",
            "hub2.device.azure-devices.net",
        ]

    def test_dict_to_service(self):
        result = {"iotHubs": ["hub1.azure-devices.net"]}
        _transform_enrollment_hub_hostnames(result, HostnameType.SERVICE.value)
        assert result["iotHubs"] == ["hub1.service.azure-devices.net"]

    def test_dict_no_iot_hubs_key(self):
        result = {"registrationId": "test1"}
        _transform_enrollment_hub_hostnames(result, HostnameType.DEVICE.value)
        assert "iotHubs" not in result

    def test_dict_empty_iot_hubs(self):
        result = {"iotHubs": []}
        _transform_enrollment_hub_hostnames(result, HostnameType.DEVICE.value)
        assert not result["iotHubs"]

    def test_dict_gov_cloud(self):
        result = {"iotHubs": ["hub1.azure-devices.us"]}
        _transform_enrollment_hub_hostnames(result, HostnameType.DEVICE.value)
        assert result["iotHubs"] == ["hub1.device.azure-devices.us"]

    # --- Model object results (from create/update) ---

    def test_model_to_device(self):
        model = MagicMock()
        model.iot_hubs = ["hub1.azure-devices.net", "hub2.azure-devices.net"]
        _transform_enrollment_hub_hostnames(model, HostnameType.DEVICE.value)
        assert model.iot_hubs == [
            "hub1.device.azure-devices.net",
            "hub2.device.azure-devices.net",
        ]

    def test_model_to_service(self):
        model = MagicMock()
        model.iot_hubs = ["hub1.azure-devices.net"]
        _transform_enrollment_hub_hostnames(model, HostnameType.SERVICE.value)
        assert model.iot_hubs == ["hub1.service.azure-devices.net"]

    def test_model_none_iot_hubs(self):
        model = MagicMock()
        model.iot_hubs = None
        _transform_enrollment_hub_hostnames(model, HostnameType.DEVICE.value)
        assert model.iot_hubs is None

    def test_model_classic_noop(self):
        model = MagicMock()
        model.iot_hubs = ["hub1.azure-devices.net"]
        _transform_enrollment_hub_hostnames(model, HostnameType.CLASSIC.value)
        assert model.iot_hubs == ["hub1.azure-devices.net"]

    # --- List results (from list commands) ---

    def test_list_of_dicts(self):
        results = [
            {"iotHubs": ["hub1.azure-devices.net"]},
            {"iotHubs": ["hub2.azure-devices.net"]},
        ]
        transformed = _transform_enrollment_hub_hostnames(results, HostnameType.DEVICE.value)
        assert transformed[0]["iotHubs"] == ["hub1.device.azure-devices.net"]
        assert transformed[1]["iotHubs"] == ["hub2.device.azure-devices.net"]

    def test_list_classic_noop(self):
        results = [{"iotHubs": ["hub1.azure-devices.net"]}]
        transformed = _transform_enrollment_hub_hostnames(results, HostnameType.CLASSIC.value)
        assert transformed[0]["iotHubs"] == ["hub1.azure-devices.net"]

    def test_empty_list(self):
        assert not _transform_enrollment_hub_hostnames([], HostnameType.DEVICE.value)

    # --- Edge cases ---

    def test_none_result(self):
        assert _transform_enrollment_hub_hostnames(None, HostnameType.DEVICE.value) is None

    def test_default_resolves_to_device(self):
        result = {"iotHubs": ["hub1.azure-devices.net"]}
        _transform_enrollment_hub_hostnames(result)
        assert result["iotHubs"] == ["hub1.device.azure-devices.net"]

    def test_auto_resolves_to_device(self):
        result = {"iotHubs": ["hub1.azure-devices.net"]}
        _transform_enrollment_hub_hostnames(result, HostnameType.AUTO.value)
        assert result["iotHubs"] == ["hub1.device.azure-devices.net"]

    def test_multiple_hubs_mixed_domains(self):
        result = {
            "iotHubs": [
                "hub1.azure-devices.net",
                "hub2.azure-devices.us",
                "hub3.azure-devices.cn",
            ],
        }
        _transform_enrollment_hub_hostnames(result, HostnameType.SERVICE.value)
        assert result["iotHubs"] == [
            "hub1.service.azure-devices.net",
            "hub2.service.azure-devices.us",
            "hub3.service.azure-devices.cn",
        ]


class TestTransformRegistrationHubHostname:
    """Tests for _transform_registration_hub_hostname — transforms assignedHub in registration results."""

    def test_auto_resolves_to_device(self):
        result = {"assignedHub": "hub1.azure-devices.net", "registrationId": "dev1"}
        _transform_registration_hub_hostname(result, HostnameType.AUTO.value)
        assert result["assignedHub"] == "hub1.device.azure-devices.net"

    def test_classic(self):
        result = {"assignedHub": "hub1.azure-devices.net"}
        _transform_registration_hub_hostname(result, HostnameType.CLASSIC.value)
        assert result["assignedHub"] == "hub1.azure-devices.net"

    def test_device(self):
        result = {"assignedHub": "hub1.azure-devices.net"}
        _transform_registration_hub_hostname(result, HostnameType.DEVICE.value)
        assert result["assignedHub"] == "hub1.device.azure-devices.net"

    def test_no_assigned_hub(self):
        result = {"registrationId": "dev1", "status": "unassigned"}
        _transform_registration_hub_hostname(result, HostnameType.DEVICE.value)
        assert "assignedHub" not in result

    def test_none_assigned_hub(self):
        result = {"assignedHub": None}
        _transform_registration_hub_hostname(result, HostnameType.DEVICE.value)
        assert result["assignedHub"] is None

    def test_list_of_registrations(self):
        results = [
            {"assignedHub": "hub1.azure-devices.net"},
            {"assignedHub": "hub2.azure-devices.net"},
        ]
        transformed = _transform_registration_hub_hostname(results, HostnameType.DEVICE.value)
        assert transformed[0]["assignedHub"] == "hub1.device.azure-devices.net"
        assert transformed[1]["assignedHub"] == "hub2.device.azure-devices.net"

    def test_none_result(self):
        assert _transform_registration_hub_hostname(None, HostnameType.DEVICE.value) is None

    def test_default_is_auto(self):
        result = {"assignedHub": "hub1.azure-devices.net"}
        _transform_registration_hub_hostname(result)
        assert result["assignedHub"] == "hub1.device.azure-devices.net"
