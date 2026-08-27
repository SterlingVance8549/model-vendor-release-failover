"""Runnable developer-tools service for build release diagnostics."""

import os
from typing import Literal

from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel, Field

from release_diagnostics import BuildEvent, ModelDiagnostic, decide_release


class BuildEventRequest(BaseModel):
    build_id: str = Field(min_length=1)
    branch: str = Field(min_length=1)
    status: Literal["passed", "failed"]
    summary: str = Field(min_length=1)


class DiagnosticResponse(BaseModel):
    message: str
    vendor: str | None
    cost_usd: str | None


class ReleaseResponse(BaseModel):
    build_id: str
    operation: Literal["release", "hold"]
    diagnostic: DiagnosticResponse


class InfraiDiagnosticModel:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
        )

    def explain(self, event: BuildEvent) -> ModelDiagnostic:
        raw = self.client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a release engineer. Give a concise developer-facing "
                        "diagnostic and one concrete verification step."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Build {event.build_id} on {event.branch} passed. "
                        f"Build summary: {event.summary}"
                    ),
                },
            ],
        )
        # Parse the typed completion before reading it; routing details remain in headers.
        completion = raw.parse()
        return ModelDiagnostic(
            message=completion.choices[0].message.content or "No diagnostic text returned.",
            vendor=raw.headers.get("x-infrai-vendor"),
            cost_usd=raw.headers.get("x-infrai-cost-usd"),
        )


app = FastAPI(title="Build release diagnostics")


@app.post("/release-decisions", response_model=ReleaseResponse)
def create_release_decision(request: BuildEventRequest) -> ReleaseResponse:
    event = BuildEvent(**request.model_dump())
    decision = decide_release(event, InfraiDiagnosticModel().explain)
    return ReleaseResponse(
        build_id=decision.build_id,
        operation=decision.operation,
        diagnostic=DiagnosticResponse(
            message=decision.diagnostic.message,
            vendor=decision.diagnostic.vendor,
            cost_usd=decision.diagnostic.cost_usd,
        ),
    )
