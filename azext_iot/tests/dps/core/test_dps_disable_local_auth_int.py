# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Integration tests for DPS disable-local-auth (SAS key authentication)."""

from azext_iot.common.embedded_cli import EmbeddedCLI
from azext_iot.tests.generators import generate_generic_id

cli = EmbeddedCLI()


def test_dps_disable_local_auth_lifecycle(provisioned_iot_dps_no_hub_module):
    """create/update should toggle the disableLocalAuth (SAS key auth) property."""
    dps_rg = provisioned_iot_dps_no_hub_module["resourceGroup"]
    location = provisioned_iot_dps_no_hub_module["dps"]["location"]
    dps_name = f"aziotclitest-dps-{generate_generic_id()}"[:35]
    try:
        # create with SAS key (local) auth disabled
        created = cli.invoke(
            f"iot dps create -n {dps_name} -g {dps_rg} -l {location} --disable-local-auth true"
        ).as_json()
        assert created["properties"]["disableLocalAuth"] is True

        # update re-enables SAS key auth
        updated = cli.invoke(
            f"iot dps update -n {dps_name} -g {dps_rg} --disable-local-auth false"
        ).as_json()
        assert updated["properties"]["disableLocalAuth"] is False
    finally:
        cli.invoke(f"iot dps delete -n {dps_name} -g {dps_rg}")
