"""Send one successful build event through the release service."""

import json
import os
import urllib.request


event = {
    "build_id": "build-1842",
    "branch": "main",
    "status": "passed",
    "summary": "Unit tests and package checks passed.",
}
request = urllib.request.Request(
    "http://127.0.0.1:8000/release-decisions",
    data=json.dumps(event).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

if "INFRAI_API_KEY" not in os.environ:
    raise SystemExit("Set INFRAI_API_KEY before running this example.")

with urllib.request.urlopen(request) as response:
    print(json.dumps(json.load(response), indent=2))
