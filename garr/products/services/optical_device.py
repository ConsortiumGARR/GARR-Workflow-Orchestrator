# Copyright 2025 GARR.
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

from typing import Any

from orchestrator.domain.base import ProductBlockModel
from pydantic_forms.types import UUIDstr

from products.product_blocks.optical_device import (
    OpticalDeviceBlock,
    OpticalDeviceBlockProvisioning,
    Platform,
    Vendor,
)
from services.infinera import tnms_client
from utils.attributedispatch import (
    attribute_dispatch_base,
    attributedispatch,
)
from utils.custom_types.frequencies import available_to_used_passbands


@attributedispatch("vendor")
def get_nms_uuid(optical_device: ProductBlockModel) -> UUIDstr:
    """Retrieve the uuid of an optical device from its Network Management System (generic function).

    Specific implementations of this generic function MUST specify the *vendor* they work on.

    Args:
        optical_device: Optical device of which the NMS uuid is to be retrieved

    Returns:
        The UUID of the optical device in its Network Management System

    Raises:
        TypeError: in case a specific implementation could not be found. The domain model it was called for will be
            part of the error message.

    """
    return attribute_dispatch_base(get_nms_uuid, "vendor", optical_device.vendor)


@get_nms_uuid.register(Vendor.Infinera)
def _(optical_device: OpticalDeviceBlockProvisioning) -> UUIDstr:
    filter_string = optical_device.fqdn.replace(".garr.net", "")
    devices = tnms_client.data.equipment.devices.retrieve(fields=["name", "uuid"])
    devices = [
        device for device in devices if device["name"][0]["value"] == filter_string
    ]
    if len(devices) == 1:
        return devices[0]["uuid"]
    msg = f"Found {len(devices)} devices with name {filter_string}. Expected 1."
    raise ValueError(msg)


@attributedispatch("platform")
def retrieve_omses_terminating_on_device(
    optical_device: OpticalDeviceBlock,
) -> list[dict[str, Any]]:
    """
    Retrieve all the Optical Muxed Sections terminating on a given Optical Device.

    This function acts as a generic dispatcher based on the platform of the optical device.
    Specific implementations of this function must specify the platform they work on.

    Args:
        optical_device: The OpticalDeviceBlock for which Optical Muxed Sections are to be retrieved.

    Returns:
        A list of dictionaries containing information about the Optical Muxed Sections.

    Raises:
        TypeError: If a specific implementation could not be found for the given platform.

    Example return:
        [
            {
                'local_port': '1-A-2-L1',
                'remote_port': '1-A-1-L1',
                'local_device': 'flex.aa00.garr.net',
                'remote_device': 'flex.zz99.garr.net',
                'available_passbands': [
                    [191362500, 191375000],
                ]
            },
            {
                'local_port': '1-A-1-L1',
                'remote_port': '1-A-2-L1',
                'local_device': 'flex.aa00.garr.net',
                'remote_device': 'flex.bb11.garr.net',
                'available_passbands': [
                    [196062500, 196075000],
                    [196112500, 196125000],
                ]
            }
        ]
    """
    return attribute_dispatch_base(
        retrieve_omses_terminating_on_device, "platform", optical_device.platform
    )


@retrieve_omses_terminating_on_device.register(Platform.FlexILS)
def _(optical_device: OpticalDeviceBlock) -> list[dict[str, Any]]:
    response = tnms_client.flexils(
        optical_device.nms_uuid, optical_device.fqdn.replace(".garr.net", "")
    ).rtrv_otelink()
    omses = []
    for otelink in response.parsed_data:
        if otelink["REACHSCOPE"] == "Local":
            local_device, local_port = otelink["AID"].split("-", 1)
            remote_device, remote_port = otelink["MATETELINK"].split("-", 1)
            available_passbands = [
                [int(x) for x in inner_list]
                for inner_list in otelink["AVAILFREQRANGELIST"]
            ]
            local_device = f"{local_device}.garr.net"
            remote_device = f"{remote_device}.garr.net"
            omses.append(
                {
                    "local_port": local_port,
                    "remote_port": remote_port,
                    "local_device": local_device,
                    "remote_device": remote_device,
                    "available_passbands": available_passbands,
                }
            )


@attributedispatch("platform")
def retrieve_ports_spectral_occupations(
    optical_device: OpticalDeviceBlock,
) -> dict[str, list[list[int]]]:
    """
    Retrieve the spectral occupations of ports on a given Optical Device.

    This function acts as a generic dispatcher based on the platform of the optical device.
    Specific implementations of this function must specify the platform they work on.

    Args:
        optical_device: The OpticalDeviceBlock for which port spectral occupations are to be retrieved.

    Returns:
        A dictionary where keys are port names and values are lists of spectral occupations.

    Raises:
        TypeError: If a specific implementation could not be found for the given platform.

    Example return:
        {
            '1-A-2-L1': [
                [191362500, 191375000],
            ],
            '1-A-1-L1': [
                [196062500, 196075000],
                [196112500, 196125000],
            ]
        }
    """
    return attribute_dispatch_base(
        retrieve_ports_spectral_occupations, "platform", optical_device.platform
    )


@retrieve_ports_spectral_occupations.register(Platform.FlexILS)
def _(optical_device: OpticalDeviceBlock) -> dict[str, list[list[int]]]:
    spectral_occupations = {}
    response = tnms_client.flexils(
        optical_device.nms_uuid, optical_device.fqdn.replace(".garr.net", "")
    ).rtrv_otelink()
    for otelink in response.parsed_data:
        if otelink["REACHSCOPE"] == "Local":
            local_device, local_port = otelink["AID"].split("-", 1)
            if not isinstance(otelink["AVAILFREQRANGELIST"][0], list):
                otelink["AVAILFREQRANGELIST"] = [otelink["AVAILFREQRANGELIST"]]
            available_passbands = [
                [int(x) for x in inner_list]
                for inner_list in otelink["AVAILFREQRANGELIST"]
            ]
            print(available_passbands, local_device, local_port)
            spectral_occupations[local_port] = available_to_used_passbands(
                available_passbands
            )
    return spectral_occupations


@retrieve_ports_spectral_occupations.register(Platform.Groove_G30)
def _(optical_device: OpticalDeviceBlock) -> dict[str, list[list[int]]]:
    return {}

@retrieve_ports_spectral_occupations.register(Platform.GX_G42)
def _(optical_device: OpticalDeviceBlock) -> dict[str, list[list[int]]]:
    return {}
