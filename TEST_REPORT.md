# AI JanSeva — Verification Report

Date: 2026-10-24

## Automated checks run in this environment

- Python syntax compilation (`python -m py_compile app.py`): PASS
- JavaScript syntax check (`node --check static/js/app.js`): PASS
- Offline audit suite (`python tests/test_offline_audit.py`): PASS, 9 unittest methods
- Hugging Face client mock tests (`python tests/test_hf_client.py`): PASS, 4 unittest methods
- Scheme catalogue: PASS, 41 records and unique names
- Official portal URL format: PASS, all catalogue URLs use HTTPS
- Scheme guide formatting: PASS, 41 scheme entries × 5 language codes = 205 non-empty-output checks
- Targeted scheme-query regressions: PASS, 8/8
- Assistant route login-protection decorator: static check PASS
- Health route presence and environment-configurable secret key: static check PASS
- ZIP integrity: checked after packaging

## Hugging Face mock tests

The mock tests verify that the client skips calls when `HF_TOKEN` is missing, returns a parsed answer for a simulated successful response, and falls back safely on simulated HTTP/network failures without logging the token. These tests do **not** contact Hugging Face or validate a real token, provider quota, or model availability.

## Not verified here

Flask is not installed in this execution environment and package-index/network access is unavailable, so an actual Flask server/test client could not be started here. The following therefore remain unverified:

- Live Hugging Face inference, real token permissions, model/provider availability, quota, latency, or answer quality
- Registration/login/logout using a real Flask session and SQLite database
- Full browser interaction and visual rendering
- PythonAnywhere or other hosting outbound network access and deployment behavior
- Current government eligibility, deadlines, document requirements, or scheme approval

The language checks establish that the formatter returns non-empty text for each tested language code; they do not establish complete translation quality for every guide. Do not describe this project as fully production-verified until these remaining live checks pass on the target machine/account.

## Run local checks on Windows

From the extracted `AI_JanSeva_Old_Updated` project folder:

```powershell
python -m pip install -r requirements.txt
python -m py_compile app.py
python tests/test_offline_audit.py
python tests/test_hf_client.py
node --check static/js/app.js
python app.py
```

For a Hugging Face test, set `HF_TOKEN` and `HF_MODEL` in the **same PowerShell terminal that starts Flask**. Keep the token private. Send a general question (not a scheme application question, because those intentionally use deterministic application guides first). Confirm `/api/assistant` returns `mode: "huggingface"` in the Network response. A fallback response means live inference was not confirmed; check the terminal's safe error log and current Hugging Face model/provider access.
