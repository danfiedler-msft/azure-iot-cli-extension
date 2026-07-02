# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pytest

from azext_iot.tests.generators import generate_generic_id
from azext_iot.core.custom import iot_dps_create, iot_dps_update

dps_name = generate_generic_id()
resource_group = generate_generic_id()
location = "westus2"


class TestDPSCreateDisableLocalAuth:
    @pytest.mark.parametrize("disable_local_auth", [True, False, None])
    def test_create_sets_disable_local_auth(self, fixture_cmd, mocker, disable_local_auth):
        mocker.patch("azext_iot.core.custom._check_dps_name_availability")
        mocker.patch("azext_iot.core.custom._ensure_location", return_value=location)
        mock_client = mocker.MagicMock()

        iot_dps_create(
            fixture_cmd,
            mock_client,
            dps_name=dps_name,
            resource_group_name=resource_group,
            disable_local_auth=disable_local_auth,
        )

        body = mock_client.iot_dps_resource.begin_create_or_update.call_args.kwargs["iot_dps_description"]
        props = body["properties"]
        if disable_local_auth is None:
            # Omitted when not provided so the service default is preserved.
            assert "disableLocalAuth" not in props
        else:
            assert props["disableLocalAuth"] is disable_local_auth


class TestDPSUpdateDisableLocalAuth:
    @pytest.mark.parametrize("disable_local_auth", [True, False, None])
    def test_update_sets_disable_local_auth(self, mocker, disable_local_auth):
        mocker.patch("azext_iot.core.custom._ensure_dps_resource_group_name", return_value=resource_group)
        mock_client = mocker.MagicMock()
        parameters = {"properties": {}}

        iot_dps_update(
            mock_client,
            dps_name,
            parameters,
            disable_local_auth=disable_local_auth,
        )

        props = parameters["properties"]
        if disable_local_auth is None:
            assert "disableLocalAuth" not in props
        else:
            assert props["disableLocalAuth"] is disable_local_auth
