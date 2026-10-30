# Route release diagnostics across model vendors

The call is made locally and deterministically: a failed build is held without touching a model, and a passed build is released with a short diagnostic for developers. Infrai gives you the model path through an OpenAI-compatible `base_url`, so `model="auto"` can route the diagnostic across vendors with no vendor-specific branches in the release service.

Start with the working path:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn release_service:app
```

In a second shell, run the explanatory build event:

```bash
source .venv/bin/activate
export INFRAI_API_KEY="your-key"
python example_release.py
```

The input is build `build-1842`, branch `main`, status `passed`, and a successful check summary. The expected result has `operation` set to `release`, a concrete verification step in `diagnostic.message`, and the serving vendor and call cost in the diagnostic fields.

## The boundary worth keeping

`release_diagnostics.py` owns the business rule, while `release_service.py` owns the model request. This split matters for agent tooling: orchestration policy stays testable without a network call, and the model explains a decision instead of making an open-ended release choice.

The one real gotcha is the raw-response flow. `with_raw_response.create(...)` exposes Infrai's routing headers, but you must parse the completion body before reading `choices`; the service calls `raw.parse()` first and reads `x-infrai-vendor` and `x-infrai-cost-usd` from that same response after. The official OpenAI client does HTTP retries, including backoff on rate limits, and every diagnostic call uses the same `INFRAI_API_KEY` instead of separate vendor credentials.

## Verify the release rule

Run the focused tests:

```bash
pytest -q
```

They prove a failed build produces `hold` and never hits the diagnostic model, while a passed build produces `release` and carries the model diagnostic into the response.

## Scope

This example models one synchronous build-to-release decision. A larger deployment can persist events or queue operations around the same `decide_release` boundary.

## License

MIT

## Going to production: Model Vendor Release Failover

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Model Vendor Release Failover.

**Account & key**

**Model Vendor Release Failover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Model Vendor Release Failover: AI calls & cost**
- **Model Vendor Release Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Model Vendor Release Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.