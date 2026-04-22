# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pytest
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azext_iot.core.custom import _resolve_linked_hub_hostname


class TestResolveLinkedHubHostname:
    def test_device_with_tls13(self):
        hub = {"properties": {"deviceHostName": "hub.device.azure-devices.net", "hostName": "hub.azure-devices.net"}}
        assert _resolve_linked_hub_hostname(hub, "device") == "hub.device.azure-devices.net"

    def test_device_fallback_to_classic(self):
        hub = {"properties": {"hostName": "hub.azure-devices.net"}}
        assert _resolve_linked_hub_hostname(hub, "device") == "hub.azure-devices.net"

    def test_classic(self):
        hub = {"properties": {"deviceHostName": "hub.device.azure-devices.net", "hostName": "hub.azure-devices.net"}}
        assert _resolve_linked_hub_hostname(hub, "classic") == "hub.azure-devices.net"

    def test_default_is_device(self):
        hub = {"properties": {"deviceHostName": "hub.device.azure-devices.net", "hostName": "hub.azure-devices.net"}}
        assert _resolve_linked_hub_hostname(hub) == "hub.device.azure-devices.net"


class TestLinkedHubCreateValidation:
    @pytest.fixture
    def mock_deps(self, mocker):
        mocker.patch("azext_iot.core.custom.iot_hub_service_factory")
        mocker.patch("azext_iot.core.custom.iot_hub_get", return_value={
            "properties": {"deviceHostName": "hub.device.azure-devices.net", "hostName": "hub.azure-devices.net"},
            "location": "eastus2euap",
            "resourcegroup": "test-rg",
        })
        mocker.patch("azext_iot.core.custom.iot_hub_policy_get", return_value={
            "keyName": "iothubowner", "primaryKey": "testkey"
        })
        mocker.patch("azext_iot.core.custom._ensure_dps_resource_group_name", return_value="test-rg")
        mock_dps = {
            "identity": {"type": "SystemAssigned,UserAssigned"},
            "properties": {"iotHubs": []},
        }
        mocker.patch("azext_iot.core.custom.iot_dps_get", return_value=mock_dps)
        mock_client = mocker.MagicMock()
        mock_client.iot_dps_resource.begin_create_or_update.return_value = mocker.MagicMock()
        mocker.patch("azext_iot.core.custom.LongRunningOperation")
        mocker.patch("azext_iot.core.custom.iot_dps_linked_hub_list", return_value=[])
        return mock_client

    def test_mi_requires_hub_name(self, fixture_cmd, mock_deps):
        from azext_iot.core.custom import iot_dps_linked_hub_create
        with pytest.raises(RequiredArgumentMissingError, match="--hub-name"):
            iot_dps_linked_hub_create(
                cmd=fixture_cmd, client=mock_deps, dps_name="dps",
                authentication_type="SystemAssigned"
            )

    def test_user_assigned_requires_identity(self, fixture_cmd, mock_deps):
        from azext_iot.core.custom import iot_dps_linked_hub_create
        with pytest.raises(RequiredArgumentMissingError, match="--user-assigned-identity"):
            iot_dps_linked_hub_create(
                cmd=fixture_cmd, client=mock_deps, dps_name="dps",
                hub_name="hub", authentication_type="UserAssigned"
            )

    def test_service_hostname_rejected(self, fixture_cmd, mock_deps):
        from azext_iot.core.custom import iot_dps_linked_hub_create
        with pytest.raises(InvalidArgumentValueError, match="Service hostname"):
            iot_dps_linked_hub_create(
                cmd=fixture_cmd, client=mock_deps, dps_name="dps",
                connection_string="HostName=hub.service.azure-devices.net;SharedAccessKeyName=x;SharedAccessKey=y"
            )

    def test_mi_system_assigned_not_enabled(self, fixture_cmd, mock_deps, mocker):
        from azext_iot.core.custom import iot_dps_linked_hub_create
        mocker.patch("azext_iot.core.custom.iot_dps_get", return_value={
            "identity": {"type": "None"},
            "properties": {"iotHubs": []},
        })
        with pytest.raises(InvalidArgumentValueError, match="System-assigned managed identity is not enabled"):
            iot_dps_linked_hub_create(
                cmd=fixture_cmd, client=mock_deps, dps_name="dps",
                hub_name="hub", authentication_type="SystemAssigned"
            )

    def test_mi_with_connection_string_rejected(self, fixture_cmd, mock_deps):
        from azext_iot.core.custom import iot_dps_linked_hub_create
        with pytest.raises(MutuallyExclusiveArgumentError, match="--connection-string cannot be used with --authentication-type"):
            iot_dps_linked_hub_create(
                cmd=fixture_cmd, client=mock_deps, dps_name="dps",
                hub_name="hub", authentication_type="SystemAssigned",
                connection_string="HostName=hub.azure-devices.net;SharedAccessKeyName=x;SharedAccessKey=y"
            )

    def test_mi_null_identity_on_dps(self, fixture_cmd, mock_deps, mocker):
        from azext_iot.core.custom import iot_dps_linked_hub_create
        mocker.patch("azext_iot.core.custom.iot_dps_get", return_value={
            "identity": None,
            "properties": {"iotHubs": []},
        })
        with pytest.raises(InvalidArgumentValueError, match="System-assigned managed identity is not enabled"):
            iot_dps_linked_hub_create(
                cmd=fixture_cmd, client=mock_deps, dps_name="dps",
                hub_name="hub", authentication_type="SystemAssigned"
            )
