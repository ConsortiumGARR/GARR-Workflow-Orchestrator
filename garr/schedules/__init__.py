"""
Modulo per la registrazione di task schedulati da eseguire periodicamente.

Questo modulo estende l'elenco globale `ALL_SCHEDULERS` con nuovi task schedulati
definiti localmente, come ad esempio `run_test_native_scheduler`.

Task schedulati predefiniti disponibili nel pacchetto:
    - run_resume_workflows
    - vacuum_tasks
    - validate_subscriptions
    - validate_products

Questo modulo è utile per includere schedulazioni aggiuntive, come test o task
custom, durante l'esecuzione dell'orchestratore.
"""

from orchestrator.schedules import ALL_SCHEDULERS

ALL_SCHEDULERS.extend([])
