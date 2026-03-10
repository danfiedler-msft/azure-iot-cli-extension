# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest.mock import Mock

import pytest
from azure.cli.core.azclierror import InvalidArgumentValueError

from azext_iot.common.shared import HostnameType
from azext_iot.operations.hub import (
    _build_device_or_module_connection_string,
    _resolve_hostname_by_type,
)


class TestResolveHostnameByType:
    """Tests for _resolve_hostname_by_type helper."""

    def _make_hub(self, host_name="myhub.azure-devices.net", device_host_name=None, service_host_name=None):
        hub = Mock()
        hub.properties.host_name = host_name
        hub.properties.device_host_name = device_host_name
        hub.properties.service_host_name = service_host_name
        return hub

    def test_classic_returns_host_name(self):
        hub = self._make_hub()
        result = _resolve_hostname_by_type(hub, HostnameType.classic.value)
        assert result == "myhub.azure-devices.net"

    def test_device_returns_device_host_name(self):
        hub = self._make_hub(device_host_name="myhub.device.azure-devices.net")
        result = _resolve_hostname_by_type(hub, HostnameType.device.value)
        assert result == "myhub.device.azure-devices.net"

    def test_service_returns_service_host_name(self):
        hub = self._make_hub(service_host_name="myhub.service.azure-devices.net")
        result = _resolve_hostname_by_type(hub, HostnameType.service.value)
        assert result == "myhub.service.azure-devices.net"

    def test_device_raises_when_not_available(self):
        hub = self._make_hub(device_host_name=None)
        with pytest.raises(InvalidArgumentValueError, match="device hostname is not available"):
            _resolve_hostname_by_type(hub, HostnameType.device.value)

    def test_service_raises_when_not_available(self):
        hub = self._make_hub(service_host_name=None)
        with pytest.raises(InvalidArgumentValueError, match="service hostname is not available"):
            _resolve_hostname_by_type(hub, HostnameType.service.value)


class TestBuildConnectionStringHostnameOverride:
    """Tests for _build_device_or_module_connection_string with hostname_override."""

    def _make_device_entity(self):
        return {
            "hub": "myhub.azure-devices.net",
            "deviceId": "device1",
            "authentication": {
                "type": "sas",
                "symmetricKey": {
                    "primaryKey": "primary123",
                    "secondaryKey": "secondary456",
                },
            },
        }

    def _make_module_entity(self):
        entity = self._make_device_entity()
        entity["moduleId"] = "module1"
        return entity

    def test_device_default_uses_entity_hub(self):
        entity = self._make_device_entity()
        cs = _build_device_or_module_connection_string(entity)
        assert cs.startswith("HostName=myhub.azure-devices.net;")
        assert "DeviceId=device1" in cs

    def test_device_with_hostname_override(self):
        entity = self._make_device_entity()
        cs = _build_device_or_module_connection_string(
            entity, hostname_override="myhub.device.azure-devices.net"
        )
        assert cs.startswith("HostName=myhub.device.azure-devices.net;")
        assert "DeviceId=device1" in cs

    def test_module_with_hostname_override(self):
        entity = self._make_module_entity()
        cs = _build_device_or_module_connection_string(
            entity, hostname_override="myhub.service.azure-devices.net"
        )
        assert cs.startswith("HostName=myhub.service.azure-devices.net;")
        assert "DeviceId=device1" in cs
        assert "ModuleId=module1" in cs

    def test_device_secondary_key(self):
        entity = self._make_device_entity()
        cs = _build_device_or_module_connection_string(entity, key_type="secondary")
        assert "SharedAccessKey=secondary456" in cs

    def test_device_override_does_not_affect_key(self):
        entity = self._make_device_entity()
        cs = _build_device_or_module_connection_string(
            entity, hostname_override="override.host.net"
        )
        assert "SharedAccessKey=primary123" in cs


class TestHostnameTypeEnum:
    """Tests for HostnameType enum."""

    def test_enum_values(self):
        assert HostnameType.classic.value == "classic"
        assert HostnameType.device.value == "device"
        assert HostnameType.service.value == "service"

    def test_enum_has_three_members(self):
        assert len(HostnameType) == 3
