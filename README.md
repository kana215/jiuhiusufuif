# Whisper (faster-whisper) → Jira on Streamlit

A minimal Streamlit app that:
1) Accepts audio/video uploads
2) Converts them to mono 16k WAV (ships its own ffmpeg via imageio-ffmpeg downloader)
3) Transcribes with **faster-whisper** (CTranslate2, CPU-friendly, int8 by default)
4) Extracts tasks from the transcript (simple rules; replace with your LLM if desired)
5) Creates Jira issues via REST API

## Deploy on Streamlit Cloud

1. Push this folder to a Git repo (GitHub).
2. In Streamlit Cloud, create a new app from that repo.
3. Make sure these files are present at repo root:
   - `app.py`
   - `requirements.txt`
   - `packages.txt` (installs ffmpeg)
   - `runtime.txt` (Python 3.11)
   - `.streamlit/config.toml`
4. In Streamlit Cloud → App → Settings → **Secrets**, paste:

```
JIRA_URL = "https://your-domain.atlassian.net"
JIRA_EMAIL = "you@example.com"
JIRA_API = "your_api_token"
JIRA_PROJECT = "ABC"
```

(Do *not* commit secrets to git.)

### Avoiding pip notice/build failures
The pip upgrade notice is harmless. If build fails, the real cause is usually a dependency build error.
**Fixes:**
- Pin versions (see `requirements.txt`).
- Ensure system packages via `packages.txt`.
- Use Python 3.11 via `runtime.txt`.
- If you still see failures, check Streamlit Cloud build logs.

### Model size & RAM
- `medium` works with `compute_type=int8` on CPU-only hosts, but memory can be tight.
- If you hit OOM, try `int8_float16` or `small`.
- First run will download model weights; subsequent runs are cached.

### Local dev
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Replace rules with LLM
Swap out `extract_tasks_from_text` with your preferred LLM call to improve accuracy (e.g., OpenAI, local model).
