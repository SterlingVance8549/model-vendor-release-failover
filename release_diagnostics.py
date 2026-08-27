"""Release decisions and AI diagnostics for build events."""

from dataclasses import dataclass
from collections.abc import Callable


@dataclass(frozen=True)
class BuildEvent:
    build_id: str
    branch: str
    status: str
    summary: str


@dataclass(frozen=True)
class ModelDiagnostic:
    message: str
    vendor: str | None
    cost_usd: str | None


@dataclass(frozen=True)
class ReleaseDecision:
    build_id: str
    operation: str
    diagnostic: ModelDiagnostic


def decide_release(
    event: BuildEvent, explain: Callable[[BuildEvent], ModelDiagnostic]
) -> ReleaseDecision:
    """Keep a failed build out of release; explain successful builds with the model."""
    if event.status != "passed":
        return ReleaseDecision(
            build_id=event.build_id,
            operation="hold",
            diagnostic=ModelDiagnostic(
                message=f"Build {event.build_id} is held because its status is {event.status}.",
                vendor=None,
                cost_usd=None,
            ),
        )

    return ReleaseDecision(
        build_id=event.build_id,
        operation="release",
        diagnostic=explain(event),
    )
