from release_diagnostics import BuildEvent, ModelDiagnostic, decide_release


class RecordingModel:
    def __init__(self) -> None:
        self.events: list[BuildEvent] = []

    def explain(self, event: BuildEvent) -> ModelDiagnostic:
        self.events.append(event)
        return ModelDiagnostic("Checks are green; verify the canary.", "vendor-a", "0.001")


def test_failed_build_is_held_without_model_call() -> None:
    model = RecordingModel()
    event = BuildEvent("build-9", "main", "failed", "Type check failed")

    decision = decide_release(event, model.explain)

    assert decision.operation == "hold"
    assert decision.diagnostic.vendor is None
    assert model.events == []


def test_passed_build_is_released_with_diagnostic() -> None:
    model = RecordingModel()
    event = BuildEvent("build-10", "main", "passed", "All checks passed")

    decision = decide_release(event, model.explain)

    assert decision.operation == "release"
    assert decision.diagnostic.vendor == "vendor-a"
    assert model.events == [event]
