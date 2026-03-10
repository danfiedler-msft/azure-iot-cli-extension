# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pytest

from azext_iot.sdk.iothub.mgmt.models import GatewayVersion, IotHubDetails, IotHubProperties


class TestIotHubTls13Models:
    """Tests for TLS 1.3 related model properties (device_host_name, service_host_name, iot_hub_details)."""

    def test_iot_hub_properties_has_new_hostname_fields(self):
        """IotHubProperties should have device_host_name and service_host_name as read-only fields."""
        props = IotHubProperties()
        assert props.device_host_name is None
        assert props.service_host_name is None

    def test_iot_hub_properties_has_iot_hub_details(self):
        """IotHubProperties should have iot_hub_details as a read-only field."""
        props = IotHubProperties()
        assert props.iot_hub_details is None

    def test_iot_hub_properties_hostname_fields_in_attribute_map(self):
        """New hostname fields should map to correct JSON keys."""
        attr_map = IotHubProperties._attribute_map
        assert "device_host_name" in attr_map
        assert attr_map["device_host_name"]["key"] == "deviceHostName"
        assert "service_host_name" in attr_map
        assert attr_map["service_host_name"]["key"] == "serviceHostName"
        assert "iot_hub_details" in attr_map
        assert attr_map["iot_hub_details"]["key"] == "iotHubDetails"

    def test_iot_hub_properties_hostname_fields_are_readonly(self):
        """New hostname and iot_hub_details fields should be marked as read-only."""
        validation = IotHubProperties._validation
        assert validation["device_host_name"] == {"readonly": True}
        assert validation["service_host_name"] == {"readonly": True}
        assert validation["iot_hub_details"] == {"readonly": True}

    def test_iot_hub_details_model(self):
        """IotHubDetails should have a read-only gateway_version field."""
        details = IotHubDetails()
        assert details.gateway_version is None

    def test_iot_hub_details_gateway_version_attribute_map(self):
        """IotHubDetails gateway_version should map to correct JSON key."""
        attr_map = IotHubDetails._attribute_map
        assert "gateway_version" in attr_map
        assert attr_map["gateway_version"]["key"] == "gatewayVersion"

    def test_iot_hub_details_gateway_version_is_readonly(self):
        """IotHubDetails gateway_version should be read-only."""
        validation = IotHubDetails._validation
        assert validation["gateway_version"] == {"readonly": True}

    @pytest.mark.parametrize("version", ["V1", "V2"])
    def test_gateway_version_enum_values(self, version):
        """GatewayVersion enum should have V1 and V2 values."""
        gv = GatewayVersion(version)
        assert gv.value == version

    def test_gateway_version_enum_case_insensitive(self):
        """GatewayVersion enum should be case insensitive."""
        assert GatewayVersion("v1") == GatewayVersion.V1
        assert GatewayVersion("v2") == GatewayVersion.V2
