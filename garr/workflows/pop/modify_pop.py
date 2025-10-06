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

from re import match
from typing import Annotated

import structlog
from orchestrator.domain import SubscriptionModel
from orchestrator.forms import FormPage
from orchestrator.types import SubscriptionLifecycle
from orchestrator.workflow import StepList, begin, step
from orchestrator.workflows.steps import set_status
from orchestrator.workflows.utils import modify_workflow
from pydantic import Field, model_validator
from pydantic_forms.types import FormGenerator, State, UUIDstr

from products.product_types.pop import PoP, PopProvisioning
from utils.custom_types.coordinates import LatitudeCoordinate, LongitudeCoordinate


def subscription_description(subscription: SubscriptionModel) -> str:
    """Generate subscription description.

    The suggested pattern is to implement a subscription service that generates a subscription specific
    description, in case that is not present the description will just be set to the product name.
    """
    return f"{subscription.pop.full_name} (Point of Presence)"


logger = structlog.get_logger(__name__)


def initial_input_form_generator(subscription_id: UUIDstr) -> FormGenerator:
    subscription = PoP.from_subscription(subscription_id)

    Instruction = Annotated[
        str,
        Field(
            "Select or enter only the fields you want to modify. "
            "The subscription will be updated with the new values.",
            title="ℹ️ℹ️ℹ️ Instruction ℹ️ℹ️ℹ️",
            json_schema_extra={
                "disabled": True,
            },
        ),
    ]

    # Updated form fields to be optional and modifiable
    class ModifyPopForm(FormPage):
        instruction: Instruction

        garrxdb_id: int | None = None
        netbox_id: int | None = None
        code: str | None = None
        full_name: str | None = None
        latitude: LatitudeCoordinate | None = None
        longitude: LongitudeCoordinate | None = None

        @model_validator(mode="after")
        def validate_code(self) -> "ModifyPopForm":
            if self.code and not match(r"^[A-Z0-9]{4}$", self.code):
                msg = "code must be 4 uppercase alphanumeric characters, e.g. 'AZ99'"
                raise ValueError(
                    msg
                )
            return self

    user_input = yield ModifyPopForm
    user_input_dict = user_input.dict()

    return user_input_dict | {"subscription": subscription}


# Updated step to accept and process modifications
@step("Update subscription")
def update_subscription(
    subscription: PopProvisioning,
    garrxdb_id: int | None,
    netbox_id: int | None,
    code: str | None,
    full_name: str | None,
    latitude: LatitudeCoordinate | None,
    longitude: LongitudeCoordinate | None,
) -> State:
    pop = subscription.pop

    if garrxdb_id is not None:
        pop.garrxdb_id = garrxdb_id
    if netbox_id is not None:
        pop.netbox_id = netbox_id
    if code is not None:
        pop.code = code
    if full_name is not None:
        pop.full_name = full_name
    if latitude is not None:
        pop.latitude = latitude
    if longitude is not None:
        pop.longitude = longitude

    return {"subscription": subscription}


@step("Update subscription description")
def update_subscription_description(subscription: PoP) -> State:
    subscription.description = subscription_description(subscription)
    return {"subscription": subscription}


additional_steps = begin


@modify_workflow(
    "Modify pop",
    initial_input_form=initial_input_form_generator,
    additional_steps=additional_steps,
)
def modify_pop() -> StepList:
    return (
        begin
        >> set_status(SubscriptionLifecycle.PROVISIONING)
        >> update_subscription
        >> update_subscription_description
        >> set_status(SubscriptionLifecycle.ACTIVE)
    )
