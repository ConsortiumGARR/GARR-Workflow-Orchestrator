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

from typing import TypeAlias, cast

import structlog
from orchestrator.forms import FormPage
from orchestrator.forms.validators import Divider
from orchestrator.targets import Target
from orchestrator.types import SubscriptionLifecycle
from orchestrator.workflow import StepList, begin, step
from orchestrator.workflows.steps import set_status, store_process_subscription
from orchestrator.workflows.utils import create_workflow
from pydantic import ConfigDict, model_validator
from pydantic_forms.types import FormGenerator, State, UUIDstr
from pydantic_forms.validators import Choice

from products.product_blocks.optical_device import DeviceType
from products.product_blocks.optical_fiber import (
    OpticalDevicePortBlock,
    OpticalDevicePortBlockInactive,
)
from products.product_blocks.optical_spectrum_section import (
    OpticalSpectrumSectionBlockInactive,
)
from products.product_types.optical_device import OpticalDevice
from products.product_types.optical_fiber import OpticalFiber
from products.product_types.optical_spectrum import (
    OpticalSpectrum,
    OpticalSpectrumInactive,
    OpticalSpectrumProvisioning,
)
from products.services.optical_device import retrieve_ports_spectral_occupations
from products.services.optical_device_port import (
    set_port_description,
)
from products.services.optical_spectrum import deploy_optical_circuit
from utils.custom_types.frequencies import Frequency, Passband
from workflows.optical_device.shared import (
    multiple_optical_device_selector,
    optical_port_selector,
)
from workflows.optical_spectrum.shared import find_constrained_shortest_path
from workflows.shared import active_subscription_selector, create_summary_form


def subscription_description(
    subscription: OpticalSpectrumInactive | OpticalSpectrumProvisioning | OpticalSpectrum,
) -> str:
    """Generate subscription description.

    The suggested pattern is to implement a subscription service that generates a subscription specific
    description, in case that is not present the description will just be set to the product name.
    """
    spectrum = subscription.optical_spectrum
    return f"{spectrum.spectrum_name}"


logger = structlog.get_logger(__name__)


def initial_input_form_generator(product_name: str) -> FormGenerator:
    PartnerChoice: TypeAlias = cast(
        type[Choice], active_subscription_selector("Partner")
    )
    SrcOpticalDeviceChoice: TypeAlias = cast(
        type[Choice],
        active_subscription_selector(
            "OpticalDevice", prompt="Select source Optical Device"
        ),
    )
    DstOpticalDeviceChoice: TypeAlias = cast(
        type[Choice],
        active_subscription_selector(
            "OpticalDevice", prompt="Select destination Optical Device"
        ),
    )
    OPTICAL_DEVICE_TYPES = [
        DeviceType.ROADM,
        DeviceType.TransponderAndOADM,
        DeviceType.Amplifier,
    ]
    ExcludeOpticalDeviceChoiceList: TypeAlias = cast(
        type[list[Choice]],
        multiple_optical_device_selector(
            device_types=OPTICAL_DEVICE_TYPES,
            prompt="Exclude these Optical Devices from the Optical Spectrum",
        ),
    )
    ExcludeSpanChoiceList: TypeAlias = cast(
        type[list[Choice]],
        multiple_optical_device_selector(
            device_types=OPTICAL_DEVICE_TYPES,
            prompt="Exclude these Optical Fibers (Spans) from the Optical Spectrum",
        ),
    )

    class OpticalSpectrumInputForm(FormPage):
        """Form for inputing service name and min and max frequencies."""

        model_config = ConfigDict(title=product_name)

        optical_spectrum_name: str
        partner_id: PartnerChoice
        frequency_min: Frequency
        frequency_max: Frequency

        @model_validator(mode="after")
        def validate_frequencies(self) -> "OpticalSpectrumInputForm":
            if self.frequency_min > self.frequency_max:
                msg = "Max frequency must be greater than min frequency. Did you make a typo?"
                raise ValueError(
                    msg
                )
            return self

    user_input = yield OpticalSpectrumInputForm
    user_input_dict = user_input.dict()

    class OpticalSpectrumSrcDstForm(FormPage):
        """Form for selecting source and destination optical devices."""

        model_config = ConfigDict(title=product_name)

        src_optical_device_id: SrcOpticalDeviceChoice
        dst_optical_device_id: DstOpticalDeviceChoice

        @model_validator(mode="after")
        def validate_separate_nodes(self) -> "OpticalSpectrumSrcDstForm":
            if self.dst_optical_device_id == self.src_optical_device_id:
                msg = "Destination Optical Device cannot be the same as Source Optical Device"
                raise ValueError(
                    msg
                )
            return self

    user_input = yield OpticalSpectrumSrcDstForm
    user_input_dict.update(user_input.dict())

    SrcOpticalPortSelector: TypeAlias = cast(
        type[Choice],
        optical_port_selector(
            user_input_dict["src_optical_device_id"],
            prompt="Select source Add/Drop Port",
        ),
    )
    DstOpticalPortSelector: TypeAlias = cast(
        type[Choice],
        optical_port_selector(
            user_input_dict["dst_optical_device_id"],
            prompt="Select destination Add/Drop Port",
        ),
    )

    class OpticalSpectrumAddDropForm(FormPage):
        """Form for selecting source and destination add/drop ports."""

        model_config = ConfigDict(title=product_name)

        src_optical_port_name: SrcOpticalPortSelector
        dst_optical_port_name: DstOpticalPortSelector

    user_input = yield OpticalSpectrumAddDropForm
    user_input_dict.update(user_input.dict())

    class OpticalSpectrumConstraintsForm(FormPage):
        """Form for specifying which optical device MUST or MUST NOT be traversed by the optical spectrum."""

        model_config = ConfigDict(title=product_name)

        exclude_devices_list: ExcludeOpticalDeviceChoiceList
        divider1: Divider
        exclude_fibers_list: ExcludeSpanChoiceList

    user_input = yield OpticalSpectrumConstraintsForm
    user_input_dict.update(user_input.dict())

    summary_fields = [
        "partner_id",
        "optical_spectrum_name",
        "frequency_min",
        "frequency_max",
        "src_optical_device_id",
        "dst_optical_device_id",
        "src_optical_port_name",
        "dst_optical_port_name",
        "exclude_devices_list",
        "exclude_fibers_list",
    ]
    yield from create_summary_form(user_input_dict, product_name, summary_fields)

    return user_input_dict


@step("Saving input data into the optical spectrum model")
def create_optical_spectrum_model(
    product: UUIDstr,
    partner_id: UUIDstr,
    optical_spectrum_name: str,
    frequency_min: Frequency,
    frequency_max: Frequency,
    exclude_devices_list: list[UUIDstr],
    exclude_fibers_list: list[UUIDstr],
) -> State:
    # create subscription instance
    subscription = OpticalSpectrumInactive.from_product_id(
        product_id=product,
        customer_id=partner_id,
        status=SubscriptionLifecycle.INITIAL,
    )

    # set attributes: name
    subscription.optical_spectrum.spectrum_name = optical_spectrum_name

    # set attributes: passband
    passband: Passband = (frequency_min, frequency_max)
    subscription.optical_spectrum.passband = passband

    # set attributes: optical_spectrum_constraints
    constraints = subscription.optical_spectrum.optical_spectrum_path_constraints
    for sub_id in exclude_devices_list:
        sub = OpticalDevice.from_subscription(sub_id)
        constraints.exclude_nodes.append(sub.optical_device)
    for sub_id in exclude_fibers_list:
        sub = OpticalFiber.from_subscription(sub_id)
        constraints.exclude_spans.append(sub.optical_fiber)

    return {
        "subscription": subscription,
        "subscription_id": subscription.subscription_id,  # necessary to be able to use older generic step functions
    }


@step("Computing the constrained shortest fiber route (Breadth-First Search)")
def compute_constrained_shortest_path(
    subscription: OpticalSpectrumInactive,
    src_optical_device_id: UUIDstr,
    dst_optical_device_id: UUIDstr,
) -> State:
    src_device_subscription = OpticalDevice.from_subscription(src_optical_device_id)
    dst_device_subscription = OpticalDevice.from_subscription(dst_optical_device_id)
    src_device = src_device_subscription.optical_device
    dst_device = dst_device_subscription.optical_device
    constraints = subscription.optical_spectrum.optical_spectrum_path_constraints
    passband = subscription.optical_spectrum.passband
    ports_route = find_constrained_shortest_path(
        src_device, dst_device, passband, constraints
    )

    return {
        "ports_route": ports_route,
    }


@step("Dividing the fiber route into single-device-family sections")
def divide_path_into_sections(
    subscription: OpticalSpectrumInactive,
    ports_route: list[dict],
    src_optical_device_id: UUIDstr,
    dst_optical_device_id: UUIDstr,
    src_optical_port_name: str,
    dst_optical_port_name: str,
) -> State:
    src_device_subscription = OpticalDevice.from_subscription(src_optical_device_id)
    dst_device_subscription = OpticalDevice.from_subscription(dst_optical_device_id)
    src_device = src_device_subscription.optical_device
    dst_device = dst_device_subscription.optical_device

    # Source Add/Drop Port
    src_port = OpticalDevicePortBlockInactive.new(
        subscription_id=subscription.subscription_id,
        port_name=src_optical_port_name,
        optical_device=src_device,
        port_description=f"Remotely connected to {dst_device.fqdn} {dst_optical_port_name} via {subscription.optical_spectrum.spectrum_name}. ",
    )
    # Destination Add/Drop Port
    dst_port = OpticalDevicePortBlockInactive.new(
        subscription_id=subscription.subscription_id,
        port_name=dst_optical_port_name,
        optical_device=dst_device,
        port_description=f"Remotely connected to {src_device.fqdn} {src_optical_port_name} via {subscription.optical_spectrum.spectrum_name}. ",
    )

    def split_into_platform_sections(
        port_instance_ids: list[OpticalDevicePortBlock],
        source_port: OpticalDevicePortBlockInactive,
        destination_port: OpticalDevicePortBlockInactive,
    ) -> list[list[OpticalDevicePortBlock]]:
        """Split ports into sections based on device platform."""
        ports.append(destination_port)

        sections: list[list[OpticalDevicePortBlock]] = []
        current_section = [source_port]
        previous_port = source_port
        for current_port in ports:
            if (
                current_port.optical_device.platform
                != previous_port.optical_device.platform
            ):
                sections.append(current_section)
                current_section = []
            current_section.append(current_port)
            previous_port = current_port

        if current_section:
            sections.append(current_section)

        return sections

    ports = []
    for port in ports_route:
        port = OpticalDevicePortBlock.from_db(port["subscription_instance_id"])
        ports.append(port)
    platform_sections = split_into_platform_sections(ports, src_port, dst_port)

    optical_spectrum_sections = subscription.optical_spectrum.optical_spectrum_sections
    for section in platform_sections:
        s = OpticalSpectrumSectionBlockInactive.new(
            subscription_id=subscription.subscription_id,
            add_drop_ports=[section[0], section[-1]],
            optical_path=section[1:-1],
        )
        optical_spectrum_sections.append(s)

    return {
        "subscription": subscription,
    }


@step("Adding a description to the add/drop ports")
def configure_add_drop_ports_description(
    subscription: OpticalSpectrumProvisioning,
) -> State:
    oss = subscription.optical_spectrum.optical_spectrum_sections
    src_port = oss[0].add_drop_ports[0]
    dst_port = oss[-1].add_drop_ports[-1]

    outputs = []
    for port in (src_port, dst_port):
        command_output = set_port_description(
            port.optical_device, port.port_name, port.port_description
        )
        outputs.append(command_output)

    return {"commands_outputs": outputs, "subscription": subscription}


@step("Provisioning optical spectrum sections")
def provision_optical_sections(subscription: OpticalSpectrumProvisioning) -> State:
    passband = subscription.optical_spectrum.passband
    spectrum_name = subscription.optical_spectrum.spectrum_name
    carrier = (int(0.5 * (passband[0] + passband[1])), passband[1] - passband[0])
    results = {}
    for section in subscription.optical_spectrum.optical_spectrum_sections:
        src_device = section.add_drop_ports[0].optical_device
        results[src_device.platform] = deploy_optical_circuit(
            src_device, section, spectrum_name, passband, carrier
        )

    return {
        "configured_optical_xcon": results,
        "subscription": subscription,
    }


@step("Updating the available passbands of any Open Line System port in the path")
def update_used_passbands(subscription: OpticalSpectrumProvisioning) -> State:
    passbands_by_device = {}
    for section in subscription.optical_spectrum.optical_spectrum_sections:
        for port in section.optical_path:
            device = port.optical_device
            if device.device_type in [
                DeviceType.ROADM,
                DeviceType.TransponderAndOADM,
            ]:
                if device.fqdn not in passbands_by_device:
                    passbands_by_device[device.fqdn] = (
                        retrieve_ports_spectral_occupations(device)
                    )
                port.used_passbands = passbands_by_device[device.fqdn].get(
                    port.port_name, []
                )

    return {"subscription": subscription}


additional_steps = begin


@create_workflow(
    "Create Optical Spectrum",
    initial_input_form=initial_input_form_generator,
    additional_steps=additional_steps,
)
def create_optical_spectrum() -> StepList:
    return (
        begin
        >> create_optical_spectrum_model
        >> store_process_subscription(Target.CREATE)
        >> compute_constrained_shortest_path
        >> divide_path_into_sections
        >> set_status(SubscriptionLifecycle.PROVISIONING)
        >> configure_add_drop_ports_description
        >> provision_optical_sections
        >> update_used_passbands
    )
