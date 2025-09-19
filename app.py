
import os
import io
import time
import json
import tempfile
import streamlit as st

from utils.audio import ensure_wav, sniff_media_type
from utils.transcribe import load_asr, transcribe_file
from utils.jira_client import JiraClient, guess_assignee, extract_tasks_from_text

st.set_page_config(page_title="Whisper (faster) → Jira", layout="centered")

st.title("🎧 Whisper (faster) → 📝 Tasks → 🧩 Jira")

with st.expander("Settings", expanded=False):
    lang = st.selectbox("Primary language hint", ["auto", "ru", "en"], index=0)
    vad = st.checkbox("Use VAD (voice activity detection)", value=False)
    compute_type = st.selectbox("Model precision", ["int8", "int8_float16", "float16", "float32"], index=0)
    beam_size = st.slider("Beam size", 1, 5, 1)
    enable_task_extraction = st.checkbox("Extract tasks from transcript", value=True)

st.write("Upload an **audio or video** file (it'll be converted to WAV automatically):")
file = st.file_uploader("Audio/Video", type=["wav","mp3","m4a","aac","flac","ogg","opus","webm","mp4","mov","mkv"], accept_multiple_files=False)

col1, col2 = st.columns(2)
with col1:
    st.caption("Jira (optional)")
    jira_url = st.text_input("Jira URL", value=st.secrets.get("JIRA_URL", ""))
    jira_email = st.text_input("Jira Email", value=st.secrets.get("JIRA_EMAIL", ""))
    jira_api = st.text_input("Jira API Token", value=st.secrets.get("JIRA_API", ""), type="password")
    jira_project = st.text_input("Jira Project Key", value=st.secrets.get("JIRA_PROJECT", ""))
with col2:
    st.caption("Model")
    model_size = st.selectbox("faster-whisper model", ["medium", "small", "base"], index=0)
    quant = st.selectbox("Quantization (smaller = less RAM)", ["q8", "q5_0", "none"], index=0)

start = st.button("Transcribe & Extract")

@st.cache_resource(show_spinner=True)
def get_asr(model_size: str, compute_type: str, quant: str, vad: bool):
    return load_asr(model_size=model_size, compute_type=compute_type, quant=quant, use_vad=vad)

if start and file is not None:
    # Persist upload to a temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    st.info("Converting to WAV (mono, 16kHz)...")
    wav_path = ensure_wav(tmp_path)

    st.success("Converted.")
    st.audio(wav_path)

    st.info("Loading ASR model (first run may take a while; cached afterwards)...")
    asr = get_asr(model_size, compute_type, quant, vad)

    st.info("Transcribing...")
    t0 = time.time()
    text, segments = transcribe_file(asr, wav_path, language=None if lang=="auto" else lang, beam_size=beam_size)
    t1 = time.time()

    st.success(f"Done in {t1 - t0:.1f}s.")
    with st.expander("Raw transcript"):
        st.code(text)

    if enable_task_extraction:
        st.info("Extracting tasks from transcript...")
        tasks = extract_tasks_from_text(text)
        st.json(tasks)

        # Guess assignee from names in text (very naive)
        assignee = guess_assignee(text)
        if assignee:
            st.write(f"Guessed assignee: **{assignee}**")

        # Create tasks in Jira if credentials provided
        if jira_url and jira_email and jira_api and jira_project:
            try:
                jc = JiraClient(jira_url, jira_email, jira_api, jira_project)
                created = []
                for t in tasks:
                    issue = jc.create_issue(summary=t["summary"], description=t.get("description",""), duedate=t.get("due_date"))
                    created.append({"key": issue["key"], "summary": t["summary"]})
                st.success("Created issues:")
                st.json(created)
            except Exception as e:
                st.error(f"Jira error: {e}")
        else:
            st.warning("Jira credentials not set. Fill in the fields to create issues automatically.")

    # Cleanup temp file
    try:
        os.remove(tmp_path)
    except Exception:
        pass
elif start and file is None:
    st.warning("Please upload a file first.")
else:
    st.caption("Tip: Medium model with int8 or int8_float16 is a good balance for Streamlit Cloud.")
