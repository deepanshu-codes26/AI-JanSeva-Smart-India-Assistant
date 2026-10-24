# AI JanSeva – Smart India Assistant (Full-Stack Project)

यह project Flask + SQLite backend और HTML/CSS/JavaScript frontend के साथ बनाया गया है।

## Features
- Responsive Hindi-first UI
- 40+ government scheme/service cards
- Server-side search and category filter
- User registration and login
- Password hashing
- Login के बाद schemes save/remove करना
- Saved Schemes page
- Profile-based starter suggestions API
- Topic-based JanSeva Help API
- FAQ, mobile navigation, official portal links
- SQLite database auto-create

## जरूरी बात
- यह शैक्षणिक prototype है, सरकारी वेबसाइट नहीं।
- Eligibility checker केवल प्रारंभिक सुझाव देता है; official eligibility निर्णय नहीं।
- JanSeva Help uses grounded application guides first for recognised scheme/process questions; general questions can use optional Hugging Face or Ollama inference when configured, with built-in guidance as fallback.
- सरकारी पोर्टल/योजनाओं के URL और नियम समय के साथ बदल सकते हैं; deployment से पहले सत्यापित करें।
- Login/session secrets और production deployment की security configuration अलग से मजबूत करनी चाहिए।

## Windows पर चलाने का तरीका

### 1. Python install करें
Python 3.10 या नया install करें। Install करते समय **Add Python to PATH** चुनें।

### 2. Project folder खोलें
ZIP extract करें। Folder में `app.py` और `requirements.txt` होने चाहिए।

### 3. Terminal खोलें
File Explorer में project folder खोलकर address bar में `cmd` लिखें और Enter दबाएँ, या VS Code में Terminal खोलें।

### 4. Virtual environment बनाएं
```bat
python -m venv .venv
.venv\Scripts\activate
```

### 5. Dependencies install करें
```bat
pip install -r requirements.txt
```

### 6. App run करें
```bat
python app.py
```

Terminal में local URL दिखाई देगा, आम तौर पर:
`http://127.0.0.1:5000`

इसे Chrome या Edge में खोलें। Database (`janseva.db`) पहली run पर बन जाएगा।

## Useful routes
- `/` — Home + scheme directory
- `/register` — Account registration
- `/login` — Login
- `/saved` — Saved schemes (login required)
- `/health` — Simple health-check endpoint

## Deployment checklist
1. `SECRET_KEY` को environment variable में मजबूत random value दें।
2. `FLASK_DEBUG=0` रखें।
3. Production WSGI server (जैसे Gunicorn) और HTTPS का उपयोग करें।
4. CSRF protection, rate limiting, secure cookies, backups और privacy notice जोड़ें।
5. कोई भी AI API key frontend में कभी न रखें; केवल server environment में रखें।
6. Official scheme details और eligibility rules को official sources से verify करें।


## Premium UI update
इस संस्करण में CSS को Apple-inspired glassmorphism, साफ spacing, बेहतर cards, responsive layout और हल्के Indian tricolour accents के साथ refresh किया गया है। Flask routes, database logic, forms और JavaScript functionality को बदला नहीं गया है।


## Premium UI V2
इस संस्करण में homepage को स्पष्ट रूप से अलग dark navy hero, saffron CTA, white scheme cards, tricolour hover accent और अधिक contrast के साथ redesign किया गया है। Backend और route logic वही रखा गया है।


## Online deployment (Render)
1. Project ko GitHub repository mein upload karein. `.env`, API keys aur `janseva.db` commit na karein.
2. Render par New + > Blueprint select karke repository connect karein; `render.yaml` service setup karega.
3. Deploy complete hone ke baad `/health` kholkar `status: ok` verify karein.
4. Important: Render ki normal filesystem persistent nahi hoti. Is setup mein SQLite database redeploy/restart par reset ho sakta hai. Real users ke persistent accounts/saved schemes ke liye persistent disk ko `DATABASE_PATH` ke saath configure karein ya managed PostgreSQL use karein.
5. Free hosting ki availability, sleep/cold starts aur limits provider ke current plan par depend karte hain.

## Production security notes
- `SECRET_KEY` hosting environment mein set hona chahiye; `render.yaml` ise generate karne ki request karta hai.
- HTTPS hosting par `COOKIE_SECURE=1` rakhein.
- Optional live AI integrations are included for Hugging Face and Ollama; they require user-supplied configuration and successful provider/network access. Built-in guidance remains the fallback.


## Optional free-tier hosted AI (PythonAnywhere)

The `/api/assistant` route now tries a Hugging Face OpenAI-compatible chat-completions endpoint when `HF_TOKEN` is configured. If the token is absent, the model is unavailable, the free quota is exhausted, or the request times out, the app returns the existing built-in guidance instead. The frontend request/response shape and the rest of the app are unchanged.

### Configure it
1. Create an account at https://huggingface.co/ and review the current Inference Providers/free-credit limits and terms.
2. Create a token with only the permissions required for inference. Do not commit it to GitHub or put it in `static/js/app.js`.
3. In PythonAnywhere, open **Web → your app → Environment variables** if available for your account/configuration, or set the variables in the WSGI file before importing the app. Prefer the dashboard's environment-variable feature where available. Set:
   - `HF_TOKEN` = your token
   - `HF_MODEL` = `Qwen/Qwen2.5-7B-Instruct` (change to a model currently supported by your inference provider)
4. Reload the web app and test the `/api/assistant` chatbot from the website. Check PythonAnywhere error logs if it always falls back.

### Free-tier and hosting limitations
- This code does not call a paid OpenAI API. Hugging Face free inference availability, model/provider support, quotas, latency and terms can change; zero-cost unlimited responses are not guaranteed.
- PythonAnywhere account/network policies may restrict outbound HTTPS requests. Verify that the account can reach `router.huggingface.co`. If outbound access is blocked, the AI request will fail and built-in guidance will be returned.
- Some models may not be available through the selected provider or may require provider-specific configuration. If the configured model fails, set `HF_MODEL` to a model currently available to your Hugging Face account.
- The app intentionally falls back to topic-based built-in guidance on AI errors; therefore a fallback response is not proof that generative AI worked.
- Never collect OTPs, passwords, UPI PINs or bank PINs in the chatbot. Verify scheme eligibility, deadlines and benefits on official government portals.


## Ollama AI integration (no paid API)

The `/api/assistant` route returns deterministic application guides for recognised scheme/process questions first. For other questions, it tries the optional Hugging Face hosted integration, then configured Ollama, and finally built-in guidance. The frontend request/response contract is unchanged.

### Run Ollama locally (development on the same PC)
1. Install Ollama from https://ollama.com/ and start it.
2. In a terminal, download a small model: `ollama pull qwen2.5:3b`.
3. Set `OLLAMA_BASE_URL=http://127.0.0.1:11434` and `OLLAMA_MODEL=qwen2.5:3b` in your local environment, then start Flask on that same computer.

### Important for PythonAnywhere
PythonAnywhere is a remote server. Setting `OLLAMA_BASE_URL=http://127.0.0.1:11434` there points to the PythonAnywhere machine, **not your personal laptop**. To use Ollama hosted on your PC, the PC must stay on and Ollama must be reachable through a secure, authenticated HTTPS tunnel/proxy. Do not port-forward or expose Ollama's unauthenticated port directly to the internet. PythonAnywhere account/network policies may also restrict outbound connections; test reachability. A safer alternative is running Ollama on a separate server you control, but that server may incur hosting/electricity costs.

### Cost and limits
Ollama software and open-weight models can be used without per-request AI API charges, subject to each model's license. Compute is not free in practical terms: your PC/server must be available and powerful enough. Remote tunnels/providers may have their own limits or costs. The app falls back to existing built-in guidance if Ollama is unavailable. A fallback answer is not proof that the AI model responded.


## Tool-using Ollama AI Agent (zero paid AI API)

For non-application questions, the `/api/assistant` route attempts the optional Hugging Face integration first, then an Ollama model configured with `OLLAMA_BASE_URL`. The Ollama integration supports a bounded tool loop with allowlisted local tools: scheme catalogue search, scheme details lookup, and general document checklist. It does not run arbitrary code, open model-provided URLs, or submit government applications. If both providers are unavailable, built-in guidance is returned.

Recommended local setup (Windows/macOS/Linux): install Ollama from https://ollama.com/download, run `ollama pull qwen2.5:3b`, set `OLLAMA_BASE_URL=http://127.0.0.1:11434` and `OLLAMA_MODEL=qwen2.5:3b`, then start Flask. Confirm your installed Ollama version/model supports tool calling.

PythonAnywhere limitation: Ollama is not installed or hosted by this Flask app. The model must run on a separate machine/server reachable from PythonAnywhere through a secured HTTPS endpoint. Do not expose port 11434 directly to the public internet. A laptop-hosted model is unavailable while the laptop is off. Hosted free inference is subject to quota, provider/model availability, outbound-network rules, latency and sleep limits. No paid AI API is called by this Ollama tool path, but zero-cost unlimited online inference is not guaranteed.

Agent verification: static Python syntax is checked; live model/tool calls and PythonAnywhere network access require testing against a running Ollama server and the target account.


## Hugging Face AI aur application guide

- General questions ke liye Hugging Face Inference Providers optional hain. `HF_TOKEN` ko server-side environment variable mein set karein; token ko `static/js/app.js` ya HTML mein kabhi na rakhein.
- Default model `Qwen/Qwen2.5-7B-Instruct` hai; provider ke current supported models, free quota aur account access ke hisaab se `HF_MODEL` badal sakte hain. Free access unlimited ya guaranteed nahi hai.
- Application-process questions (NSP scholarship aur catalogue mein listed schemes) ke liye backend step-by-step general guide aur official portal link deta hai. Ye live status/deadline checker nahi hai. Current academic-year instructions aur exact documents portal par verify karein.
- Agar `HF_TOKEN` missing ho ya hosted model fail ho, chatbot built-in guidance par fallback karta hai.
- PythonAnywhere par Web app ke environment configuration mein `HF_TOKEN`, `HF_MODEL` (optional), aur strong `SECRET_KEY` set karein; phir Web tab se Reload karein.


## Application guides for all 41 catalogue entries

- The assistant now matches application/eligibility/document questions to all 41 scheme catalogue entries.
- Each matched entry returns the catalogue's official portal, a step-by-step navigation workflow, a category-specific preparation checklist, and a warning to verify current requirements on the official portal.
- Special workflows are included for NSP, UDID/disability support, Aadhaar, DigiLocker, Passport Seva, Parivahan, PM-KISAN and PM Fasal Bima Yojana.
- The phrase "Disability Support" is treated as ambiguous: the guide distinguishes a UDID/disability certificate from other benefits instead of claiming one portal covers every benefit.
- Hindi is supported for the application guides when Hindi is selected. Other language coverage remains dependent on the translations implemented in the formatter.
- The scheme catalogue is not a live database. It does not prove current eligibility, open application windows, exact document requirements or deadlines. Users must verify these on the official portal.


## Language consistency fix
- The deterministic application-guide fallback now has explicit English output for NSP and Disability Support/UDID guides, plus English generic guide wording.
- The selected language code is still supplied by the frontend to `/api/assistant`.
- Please test English and Hindi in the browser. Bengali, Telugu, Tamil and Marathi guide translations are not yet complete for every one of the 41 entries; do not assume all scheme text is fully translated.


## Latest fix: language and Beti Bachao Beti Padhao
- Added a dedicated Beti Bachao Beti Padhao guide that recognises "can you help this scheme Beti Bachao Beti Padhao" without requiring the exact word "apply".
- The guide explains that BBBP is primarily a programme supporting the girl child and is not a universal direct-cash benefit application. It directs users to official WCD and district channels.
- Added explicit English, Hindi and Bengali guide text for BBBP.
- Updated generic built-in fallback messages to respect selected English, Hindi, Bengali, Telugu, Tamil and Marathi language settings.
- Python syntax check passed. Live browser/model testing is still required.


## Detailed guidance for all 41 catalogue entries
- Added tailored navigation/application/participation workflows and relevant preparation checklists for every catalogue entry, including education, identity documents, health services, agriculture, housing, jobs, women/child services, finance, business, digital services, and disability support.
- Scheme-name matching no longer requires the user to include words such as "apply" or "application"; natural prompts like "help me with PM-KISAN" can trigger the relevant guide.
- Guidance distinguishes direct applications from bank-led credit/insurance, local-government services, public programmes, and healthcare access. It avoids claiming that every programme is a direct cash benefit.
- Document lists are preparation aids; the exact mandatory list, eligibility, fees and dates must be verified on the official portal or implementing department.
- Catalogue count verified: 41. Python syntax check passed. Live browser/model testing is still required.


## Latest chatbot response fixes (DigiLocker and PM Surya Ghar)
- Added natural-language aliases so "How can I download my documents?" matches DigiLocker and "Explain the rooftop solar subsidy process" matches PM Surya Ghar.
- Added specific step-by-step document retrieval/download guidance for DigiLocker and rooftop solar registration, DISCOM approval, installation, commissioning and subsidy status for PM Surya Ghar.
- Added Hindi and Bengali translations for these two common guides, plus English versions.
- Fixed the guide formatter so a scheme-specific caution/message is preserved rather than overwritten by a generic disclaimer.
- Isolated tests passed for DigiLocker, PM Surya Ghar, Beti Bachao Beti Padhao and PM-KISAN guide matching/formatting. Full Flask/browser testing was not run in this environment because Flask is not installed here.


## Corrected follow-up patch
The common rooftop-solar and document-download aliases are included in `scheme_application_guide`, and the dedicated English/Hindi/Bengali response templates are included in `format_application_guide`. The Hindi generic formatter is explicitly prevented from replacing these dedicated templates. Restart the Flask server after replacing the project files.


## Offline test suite
Run `python tests/test_offline_audit.py` from this project folder to test the 41-scheme catalogue, HTTPS portal formatting, scheme guide matching, supported language-code formatting, login-protection decorator, health route and selected regressions. This does not replace live Flask/browser/Hugging Face/PythonAnywhere testing. See `TEST_REPORT.md`.
