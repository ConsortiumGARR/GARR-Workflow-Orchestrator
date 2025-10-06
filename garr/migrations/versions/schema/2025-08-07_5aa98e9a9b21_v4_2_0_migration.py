# Copyright 2025 GARR.  # noqa: INP001
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

"""add task to update the passbands of optical fibers.

Revision ID: 5aa98e9a9b21
Revises: 43ec72c4b513
Create Date: 2025-08-7 12:27:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5aa98e9a9b21"
down_revision = "43ec72c4b513"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Update workflows with name starting with "validate_"
    conn.execute(
        sa.text(
            """
            UPDATE workflows
            SET target = 'VALIDATE', is_task = TRUE
            WHERE name LIKE 'validate\\_%'
            """
        )
    )
    # Step 2: Ensure all SYSTEM and VALIDATE targets have is_task = TRUE
    conn.execute(
        sa.text(
            """
            UPDATE workflows
            SET is_task = TRUE
            WHERE target IN ('SYSTEM', 'VALIDATE')
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Attempt to reverse the changes (best-effort)
    # NOTE: original 'target' values for validate_* workflows can't be recovered unless tracked elsewhere

    # Step 1: Set validate_* workflows' target back to SYSTEM (assumption)
    conn.execute(
        sa.text(
            """
            UPDATE workflows
            SET target = 'SYSTEM'
            WHERE name LIKE 'validate\\_%'
            """
        )
    )

    # Step 2: Set is_task = FALSE where it was changed (safe assumption: only SYSTEM/VALIDATE were modified)
    conn.execute(
        sa.text(
            """
            UPDATE workflows
            SET is_task = FALSE
            WHERE target IN ('SYSTEM', 'VALIDATE')
            """
        )
    )
