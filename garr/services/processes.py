
from orchestrator.db import ProcessTable, WorkflowTable, db
from orchestrator.workflow import ProcessStatus
from pydantic_forms.types import UUIDstr
from sqlalchemy import ScalarResult, or_, select

def get_all_cleanup_tasks() -> list[WorkflowTable]:
    """Get a list of all cleanup tasks that run on a schedule."""
    return WorkflowTable.query.filter(
        or_(WorkflowTable.name == "task_clean_up_tasks", WorkflowTable.name == "task_clean_old_tasks")
    ).all()

def get_created_and_completed_processes_by_id(workflow_id: UUIDstr) -> ScalarResult:
    """Get all processes that are either created or completed, by workflow ID."""
    return db.session.scalars(
        select(ProcessTable)
        .filter(ProcessTable.is_task.is_(True))
        .filter(ProcessTable.workflow_id == workflow_id)
        .filter(
            or_(
                ProcessTable.last_status == ProcessStatus.COMPLETED.value,
                ProcessTable.last_status == ProcessStatus.CREATED.value,
            )
        )
    )

