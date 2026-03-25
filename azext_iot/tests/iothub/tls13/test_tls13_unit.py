# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pytest
from azext_iot.common.shared import HostnameType

path_fetch_tls = "azext_iot.operations.hub._fetch_tls_hostnames"
path_get_mgmt_client = "azure.cli.core.commands.client_factory.get_mgmt_service_client"


class TestResolveHostnameByType:
    """Tests for _resolve_hostname_by_type in hub.py"""

    @pytest.fixture
    def mock_hub(self, mocker):
        hub = mocker.MagicMock()
        hub.name = "testhub"
        hub.properties.host_name = "testhub.azure-devices.net"
        hub.additional_properties = {"resourcegroup": "testrg"}
        hub.location = "eastus"
        return hub

    def test_classic_returns_host_name(self, fixture_cmd, mock_hub):
        from azext_iot.operations.hub import _resolve_hostname_by_type

        result = _resolve_hostname_by_type(fixture_cmd, mock_hub, HostnameType.classic.value)
        assert result == "testhub.azure-devices.net"

    def test_default_returns_classic(self, fixture_cmd, mock_hub):
        """Default hostname_type is classic — should return classic hostname without any API call."""
        from azext_iot.operations.hub import _resolve_hostname_by_type

        result = _resolve_hostname_by_type(fixture_cmd, mock_hub, HostnameType.classic.value)
        assert result == "testhub.azure-devices.net"

    def test_device_returns_device_hostname(self, mocker, fixture_cmd, mock_hub):
        from azext_iot.operations.hub import _resolve_hostname_by_type

        mocker.patch(path_fetch_tls, return_value={
            "deviceHostName": "testhub.device.azure-devices.net",
            "serviceHostName": "testhub.service.azure-devices.net",
            "gatewayVersion": "V2",
        })
        result = _resolve_hostname_by_type(fixture_cmd, mock_hub, HostnameType.device.value)
        assert result == "testhub.device.azure-devices.net"

    def test_service_returns_service_hostname(self, mocker, fixture_cmd, mock_hub):
        from azext_iot.operations.hub import _resolve_hostname_by_type

        mocker.patch(path_fetch_tls, return_value={
            "deviceHostName": "testhub.device.azure-devices.net",
            "serviceHostName": "testhub.service.azure-devices.net",
            "gatewayVersion": "V2",
        })
        result = _resolve_hostname_by_type(fixture_cmd, mock_hub, HostnameType.service.value)
        assert result == "testhub.service.azure-devices.net"

    def test_gwv1_falls_back_to_classic(self, mocker, fixture_cmd, mock_hub):
        from azext_iot.operations.hub import _resolve_hostname_by_type

        mocker.patch(path_fetch_tls, return_value={
            "deviceHostName": None,
            "serviceHostName": None,
            "gatewayVersion": None,
        })
        result = _resolve_hostname_by_type(fixture_cmd, mock_hub, HostnameType.device.value)
        assert result == "testhub.azure-devices.net"

    def test_gwv1_falls_back_with_v1_version(self, mocker, fixture_cmd, mock_hub):
        from azext_iot.operations.hub import _resolve_hostname_by_type

        mocker.patch(path_fetch_tls, return_value={
            "deviceHostName": None,
            "serviceHostName": None,
            "gatewayVersion": "V1",
        })
        result = _resolve_hostname_by_type(fixture_cmd, mock_hub, HostnameType.service.value)
        assert result == "testhub.azure-devices.net"


class TestFetchTlsHostnames:
    """Tests for _fetch_tls_hostnames in hub.py"""

    def _setup_mock_client(self, mocker, status_code, json_data=None):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = status_code
        if json_data:
            mock_resp.json.return_value = json_data
        mock_client = mocker.MagicMock()
        mock_client.iot_hub_resource._client.send_request.return_value = mock_resp
        mock_client._config.subscription_id = "test-sub"
        mocker.patch(path_get_mgmt_client, return_value=mock_client)
        return mock_client

    def test_returns_hostnames_on_success(self, mocker, fixture_cmd):
        from azext_iot.operations.hub import _fetch_tls_hostnames

        self._setup_mock_client(mocker, 200, {
            "properties": {
                "deviceHostName": "hub1.device.azure-devices.net",
                "serviceHostName": "hub1.service.azure-devices.net",
                "iotHubDetails": {"gatewayVersion": "V2"},
            }
        })
        result = _fetch_tls_hostnames(fixture_cmd, "hub1", "rg1", "eastus")
        assert result["deviceHostName"] == "hub1.device.azure-devices.net"
        assert result["serviceHostName"] == "hub1.service.azure-devices.net"
        assert result["gatewayVersion"] == "V2"

    def test_returns_none_on_error(self, mocker, fixture_cmd):
        from azext_iot.operations.hub import _fetch_tls_hostnames

        self._setup_mock_client(mocker, 400)
        result = _fetch_tls_hostnames(fixture_cmd, "hub1", "rg1", "eastus")
        assert result["deviceHostName"] is None
        assert result["serviceHostName"] is None
        assert result["gatewayVersion"] is None

    def test_uses_regional_endpoint_for_canary(self, mocker, fixture_cmd):
        from azext_iot.operations.hub import _fetch_tls_hostnames

        mock_client = self._setup_mock_client(mocker, 200, {"properties": {}})
        _fetch_tls_hostnames(fixture_cmd, "hub1", "rg1", "eastus2euap")

        request = mock_client.iot_hub_resource._client.send_request.call_args[0][0]
        assert "eastus2euap.management.azure.com" in request.url

    def test_uses_standard_endpoint_for_non_canary(self, mocker, fixture_cmd):
        from azext_iot.operations.hub import _fetch_tls_hostnames

        mock_client = self._setup_mock_client(mocker, 200, {"properties": {}})
        _fetch_tls_hostnames(fixture_cmd, "hub1", "rg1", "eastus")

        request = mock_client.iot_hub_resource._client.send_request.call_args[0][0]
        assert "management.azure.com" in request.url
        assert "eastus2euap" not in request.url
