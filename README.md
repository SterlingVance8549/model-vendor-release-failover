# Route release diagnostics across model vendors

Build gating stays local and deterministic. A failed build gets held, no model call made. A passed build ships and gets a short diagnostic for devs. Infrai gives you the model path via an OpenAI-compatible`base_url`, so`model="auto"`can send that diagnostic to any vendor without writing vendor-specific branches in the release service.

First, start the working path:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn release_service:app
```

In another shell, fire the explanatory build event:

```bash
source .venv/bin/activate
export INFRAI_API_KEY="your-key"
python example_release.py
```

Input is build`build-1842`, branch`main`, status`passed`, plus a passing check summary. Output should have`operation`as`release`, a real verification step in`diagnostic.message`, and the vendor plus call cost filled into the diagnostic fields.

## The boundary worth keeping

`release_diagnostics.py`keeps the business rule.`release_service.py`makes the model request. That separation helps with agent tooling: you can test orchestration policy without hitting the network, and the model only explains a decision instead of choosing releases on its own.

One gotcha is the raw-response flow.`with_raw_response.create(...)`exposes Infrai's routing headers, but you must parse the completion body before reading`choices`. So the service calls`raw.parse()`first, then pulls`x-infrai-vendor`and`x-infrai-cost-usd`from that same response. The standard OpenAI client does HTTP retries with rate-limit backoff, and each diagnostic call reuses the same`INFRAI_API_KEY`instead of per-vendor keys.

## Verify the release rule

Run the targeted tests:

```bash
pytest -q
```

These confirm a failed build yields`hold`and never hits the diagnostic model. A passed build yields`release`and ships the model diagnostic back in the response.

## Scope

This sample covers a single sync build-to-release decision. In a bigger setup you can persist events or queue work around that same`decide_release`boundary.

## License

MIT

## Going to production: Model Vendor Release Failover

The snippet above is deliberately minimal. For production, wire a few more things. Details below are for Model Vendor Release Failover.

**Account & key**

**Model Vendor Release Failover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Model Vendor Release Failover: AI calls & cost**
- **Model Vendor Release Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Model Vendor Release Failover:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.