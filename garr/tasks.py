from typing import Any  # noqa: D100
from uuid import UUID

from celery import Celery
from celery.signals import setup_logging, worker_shutting_down
from nwastdlib.logging import initialise_logging
from orchestrator.db import init_database
from orchestrator.domain import SUBSCRIPTION_MODEL_REGISTRY
from orchestrator.log_config import LOGGER_OVERRIDES, logger_config
from orchestrator.services.tasks import initialise_celery
from orchestrator.settings import app_settings
from orchestrator.types import BroadcastFunc
from orchestrator.websocket import (
    broadcast_process_update_to_websocket,
    init_websocket_manager,
)
from orchestrator.websocket.websocket_manager import WebSocketManager
from orchestrator.workflows import ALL_WORKFLOWS
from structlog import get_logger

from settings import celery_settings

logger = get_logger(__name__)

LOGGER_OVERRIDES_CELERY = LOGGER_OVERRIDES | dict(
    [
        logger_config("celery"),
        logger_config("kombu"),
    ]
)


@setup_logging.connect  # type: ignore[misc]
def on_setup_logging(**kwargs: Any) -> None:  # noqa: ARG001
    """Set up logging for the Celery worker."""
    initialise_logging(additional_loggers=LOGGER_OVERRIDES_CELERY)


def process_broadcast_fn(process_id: UUID) -> None:
    """Broadcast process update to WebSocket."""
    try:
        broadcast_process_update_to_websocket(process_id)
    except Exception as e:
        logger.exception(e)  # noqa: TRY401


class OrchestratorWorker(Celery):
    """An instance that functions as a Celery worker."""

    websocket_manager: WebSocketManager
    process_broadcast_fn: BroadcastFunc

    def on_init(self) -> None:
        """Initialise a new Celery worker."""
        init_database(app_settings)

        # Prepare the wrapped_websocket_manager
        # Note: cannot prepare the redis connections here as broadcasting is async
        self.websocket_manager = init_websocket_manager(app_settings)
        self.process_broadcast_fn = process_broadcast_fn

        # Load the products and load the workflows
        import products  # noqa: PLC0415,F401
        import workflows  # noqa: PLC0415,F401

        logger.info(
            "Loaded the workflows and products",
            workflows=len(ALL_WORKFLOWS.values()),
            products=len(SUBSCRIPTION_MODEL_REGISTRY.values()),
        )

    def close(self) -> None:
        """Close Celery worker cleanly."""
        super().close()


celery = OrchestratorWorker(
    f"{app_settings.SERVICE_NAME}-worker",
    broker=celery_settings.broker_url,
    include=[
        "orchestrator.services.tasks",
    ],
)
celery.conf.update(
    result_expires=celery_settings.result_expires,
    worker_prefetch_multiplier=1,
    worker_send_task_event=True,
    task_send_sent_event=True,
    task_ignore_result=not app_settings.TESTING,
    redbeat_redis_url=celery_settings.broker_url,
)
initialise_celery(celery)

@worker_shutting_down.connect  # type: ignore[misc]
def worker_shutting_down_handler(sig, how, exitcode, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ARG001
    """Handle the Celery worker shutdown event."""
    celery.close()
