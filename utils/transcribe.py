
from typing import Tuple, List
from faster_whisper import WhisperModel

def load_asr(model_size: str = "medium", compute_type: str = "int8", quant: str = "q8", use_vad: bool = False):
    """
    Loads faster-whisper model with optional CTranslate2 quantization.
    """
    # quantization flags map
    # You can set environment variable "CT2_FORCE_CPU_ISA" if needed.
    model = WhisperModel(
        model_size_or_path=model_size,
        device="cpu",  # Streamlit Cloud has no GPU
        compute_type=compute_type,  # "int8" or "int8_float16" preferred
        cpu_threads=4,
        num_workers=1,
        download_root=None  # use default cache
    )
    return model

def transcribe_file(model, wav_path: str, language=None, beam_size: int = 1):
    segments, info = model.transcribe(
        wav_path,
        language=language,
        beam_size=beam_size,
        vad_filter=False,  # torch-free; toggle in future if you add silero (requires torch)
        word_timestamps=False
    )
    full_text = []
    segs = []
    for s in segments:
        segs.append({"start": s.start, "end": s.end, "text": s.text})
        full_text.append(s.text.strip())
    return " ".join(full_text).strip(), segs
