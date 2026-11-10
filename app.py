# -*- coding: utf-8 -*-
"""বাংলা সাবটাইটেল — BanglaASR (Streamlit Cloud)

শুধু বাংলা অডিও/ভিডিও থেকে সাবটাইটেল। মডেল: BanglaASR
(bangla-speech-processing/BanglaASR — Whisper-small, Common Voice বাংলায়
fine-tuned), CTranslate2 int8 ফরম্যাটে Hugging Face hub থেকে রানটাইমে ডাউনলোড হয়।

জেনে রাখুন: এই মডেলের বাংলা বানান Whisper turbo-র চেয়ে ভালো, কিন্তু লম্বা
অডিওতে মাঝখানের কিছু কথা বাদ পড়তে পারে — এটা মাপা আচরণ, অ্যাপের বাগ নয়।
"""
import os
import subprocess
import tempfile
import time
import wave

import numpy as np
import streamlit as st
from faster_whisper import WhisperModel

# ---- সেটিংস ---------------------------------------------------------------
MODEL_NAME = os.environ.get("WHISPER_MODEL", "muhammadantor/typly-banglaasr-ct2")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE", "int8")
MAX_SECONDS = 600          # সর্বোচ্চ ১০ মিনিট
WARN_SECONDS = 300         # ৫ মিনিটের বেশি হলে সতর্কবার্তা
AUDIO_EXTS = ["mp3", "wav", "m4a", "flac", "ogg", "aac"]
VIDEO_EXTS = ["mp4", "mov", "mkv", "webm", "avi"]
SUPPORTED = AUDIO_EXTS + VIDEO_EXTS


@st.cache_resource(show_spinner=False)
def load_model():
    return WhisperModel(MODEL_NAME, device="cpu", compute_type=COMPUTE_TYPE,
                        cpu_threads=2, num_workers=1)


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def vtt_time(seconds: float) -> str:
    return srt_time(seconds).replace(",", ".")


def to_srt(segments) -> str:
    out = []
    for i, seg in enumerate(segments, 1):
        out.append(f"{i}\n{srt_time(seg['start'])} --> {srt_time(seg['end'])}\n{seg['text'].strip()}\n")
    return "\n".join(out)


def to_vtt(segments) -> str:
    out = ["WEBVTT\n"]
    for seg in segments:
        out.append(f"{vtt_time(seg['start'])} --> {vtt_time(seg['end'])}\n{seg['text'].strip()}\n")
    return "\n".join(out)


def convert_to_wav_16k(src_path: str) -> tuple[np.ndarray, float, str]:
    """ffmpeg দিয়ে অডিও/ভিডিও থেকে 16 kHz mono WAV বানায়।

    ভিডিও হলে শুধু অডিও ট্র্যাক নেওয়া হয়। ফেরত: (samples, duration_s, wav_path)।
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src_path,
                    "-map", "0:a:0", "-ar", "16000", "-ac", "1", tmp.name], check=True)
    with wave.open(tmp.name, "rb") as w:
        duration = w.getnframes() / w.getframerate()
        raw = w.readframes(w.getnframes())
    if duration <= 0:
        os.unlink(tmp.name)
        raise ValueError("ফাইলটিতে কোনো অডিও ট্র্যাক পাওয়া যায়নি।")
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return audio, duration, tmp.name


def main():
    st.set_page_config(page_title="বাংলা সাবটাইটেল — BanglaASR", page_icon="📝", layout="centered")
    st.title("📝 বাংলা সাবটাইটেল — BanglaASR")
    st.write("শুধু বাংলা অডিও বা ভিডিও আপলোড করুন — বাংলা সাবটাইটেল (SRT / VTT) আর লেখা পাবেন।")
    st.info("এই অ্যাপ শুধু বাংলার জন্য — মডেল BanglaASR (Whisper-small, Common Voice বাংলায় শেখানো)। "
            "বানান Whisper turbo-র চেয়ে ভালো হয়, কিন্তু লম্বা অডিওতে মাঝখানের কিছু কথা বাদ পড়তে পারে।")

    uploaded = st.file_uploader("বাংলা অডিও বা ভিডিও ফাইল বেছে নিন", type=SUPPORTED)
    # ভাষা স্থির: বাংলা (এই মডেল শুধু বাংলাই জানে)
    lang_code = "bn"

    if uploaded is not None:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        suffix = "." + ext
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(uploaded.getbuffer())
            src_path = f.name
        if ext in VIDEO_EXTS:
            st.video(uploaded)
        else:
            st.audio(uploaded, format=f"audio/{ext}")

        if st.button("✍️ সাবটাইটেল বানান", type="primary"):
            try:
                with st.spinner("অডিও তৈরি হচ্ছে…"):
                    audio, duration, wav_path = convert_to_wav_16k(src_path)
                if duration > MAX_SECONDS:
                    st.error(f"অডিওটি {duration/60:.1f} মিনিট — সর্বোচ্চ {MAX_SECONDS//60} মিনিট পর্যন্ত চলবে। "
                             "ফাইলটি ছোট টুকরো করে আপলোড করুন।")
                    st.stop()
                if duration > WARN_SECONDS:
                    st.warning(f"অডিওটি {duration/60:.1f} মিনিটের — প্রসেস হতে বেশ কিছু মিনিট লাগতে পারে। "
                               "অপেক্ষা করুন, পাতা বন্ধ করবেন না।")

                with st.spinner("মডেল লোড হচ্ছে (প্রথমবার কয়েক মিনিট লাগতে পারে)…"):
                    model = load_model()
                t0 = time.time()
                with st.spinner("লেখা হচ্ছে…"):
                    segments, info = model.transcribe(
                        audio, language=lang_code, beam_size=5,
                        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
                    segs = [{"start": s.start, "end": s.end, "text": s.text.strip()}
                            for s in segments]
                elapsed = time.time() - t0
                os.unlink(wav_path)

                st.success(f"শেষ! ভাষা: বাংলা • অডিও {duration:.0f} সেকেন্ড • "
                           f"সময় লেগেছে {elapsed:.0f} সেকেন্ড (RTF {elapsed/max(duration, 1):.1f}×)")

                st.subheader("সাবটাইটেল")
                for seg in segs:
                    st.write(f"**{srt_time(seg['start'])} → {srt_time(seg['end'])}**  {seg['text']}")

                srt_text = to_srt(segs)
                vtt_text = to_vtt(segs)
                plain_text = " ".join(s["text"] for s in segs)
                base = os.path.splitext(uploaded.name)[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("⬇️ SRT ডাউনলোড", srt_text, file_name=f"{base}.srt",
                                       mime="text/plain")
                with col2:
                    st.download_button("⬇️ VTT ডাউনলোড", vtt_text, file_name=f"{base}.vtt",
                                       mime="text/vtt")
                with col3:
                    st.download_button("⬇️ শুধু লেখা (.txt)", plain_text, file_name=f"{base}.txt",
                                       mime="text/plain")
            except subprocess.CalledProcessError:
                st.error("ফাইলটি পড়া যায়নি — অন্য ফরম্যাটে দিয়ে আবার চেষ্টা করুন।")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:  # noqa: BLE001 - show the error to the user
                st.error(f"একটি সমস্যা হয়েছে: {e}")


if __name__ == "__main__":
    main()
