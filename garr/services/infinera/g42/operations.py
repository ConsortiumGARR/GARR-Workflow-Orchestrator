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

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .client import G42Client

# Registry to store all registered operations
_operation_registry: dict[str, type["OperationEndpoint"]] = {}


def register_operation(cls: type["OperationEndpoint"]) -> type["OperationEndpoint"]:
    """
    Decorator to register an operation class.

    This allows the `Operations` class to dynamically add methods for each registered operation.

    Args:
        cls: The operation class to register.

    Returns:
        The registered operation class.
    """
    _operation_registry[cls.operation_name] = cls
    return cls


class OperationEndpoint:
    """
    Base class for RESTCONF operations.

    Subclasses must define:
    - `operation_name`: The name of the operation (used as the method name in `Operations`).
    - `url_path`: The RESTCONF operation URL path.
    - `InputModel`: A Pydantic model for input validation.
    """

    operation_name: str  # Name of the operation (e.g., "create_xcon")
    url_path: str  # RESTCONF operation URL path (e.g., "ioa-services:create-xcon")
    input_model: type[BaseModel]  # Pydantic model for input validation

    def __init__(self, client: "G42Client"):
        self.client = client

    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the operation with validated input data.

        Args:
            **kwargs: Input data for the operation.

        Returns:
            The response from the RESTCONF API.
        """
        payload = self._build_payload(kwargs)
        return self.client._request("POST", f"/operations/{self.url_path}", json=payload)

    def _build_payload(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and build the payload for the operation.

        Args:
            kwargs: Input data for the operation.

        Returns:
            A dictionary representing the validated payload.
        """
        # Convert snake_case to kebab-case for input keys
        data = {k.replace("_", "-"): v for k, v in kwargs.items()}
        validated_data = self.input_model(**data).model_dump(by_alias=True, exclude_unset=True)
        return {"input": validated_data}


@register_operation
class CreateXconOperation(OperationEndpoint):
    """
    Create a cross-connect (xcon).

    Example:
        operations.create_xcon(
            source="/ioa-ne:ne/facilities/ethernet[name='1-4-T1']",
            dst_parent_odu="1-4-L1-1-ODUCni",
            direction="two-way",
            payload_type="100GBE",
            label="example",
            dst_time_slots="1..80",
            circuit_id_suffix="f001c01",
        )
    """
    operation_name = "create_xcon"
    url_path = "ioa-services:create-xcon"

    class InputModel(BaseModel):
        source: str
        dst_parent_odu: str = Field(..., alias="dst-parent-odu")
        dst_time_slots: str = Field(..., alias="dst-time-slots")
        label: str
        direction: str = Field(None)
        payload_type: str = Field(None, alias="payload-type")
        circuit_id_suffix: str = Field(None, alias="circuit-id-suffix")

    input_model = InputModel


class Operations:
    """
    A dynamic interface for invoking RESTCONF operations.

    This class dynamically adds methods for each registered operation, allowing you to call them directly.

    Example:
        import G42Client
        g42 = G42Client("192.168.42.42")
        g42.operations.create_xcon(...)

    Args:
        client (G42Client): The RESTCONF client instance used to execute operations.
    """

    def __init__(self, client: "G42Client"):
        self.client = client
        self._register_operations()

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """
        Provide dynamic access to registered operations.

        This method supports IDE static analysis tools and fallback access to dynamically
        registered operations. At runtime, all methods are registered in __init__ with _register_operations.
        If you are looking for the definition of a specific method, search its name in this file.

        Args:
            name (str): The name of the operation.

        Returns:
            Callable: A method to invoke the operation.

        Raises:
            AttributeError: If the operation is not registered.
        """
        if name in _operation_registry:
            return self._create_operation_method(_operation_registry[name])
        raise AttributeError(f"{self.__class__.__name__!r} has no operation '{name}' registered.")

    def _register_operations(self):
        """
        Dynamically add methods for registered operations.

        Each registered operation is added as a method to this class, allowing it to be called directly.
        """
        for operation_name, operation_cls in _operation_registry.items():
            setattr(self, operation_name, self._create_operation_method(operation_cls))

    def _create_operation_method(self, operation_cls: type[OperationEndpoint]) -> Callable[..., Any]:
        """
        Create a method for a specific operation.

        Args:
            operation_cls Type[OperationEndpoint]: The operation class to create a method for.

        Returns:
            Callable: A method that instantiates and executes the operation using the client.
        """
        def operation_method(**kwargs):
            operation_instance = operation_cls(self.client)
            return operation_instance.execute(**kwargs)

        operation_method.__doc__ = f"Invoke the `{operation_cls.operation_name}` operation."
        return operation_method
