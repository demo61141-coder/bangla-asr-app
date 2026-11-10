# বাংলা সাবটাইটেল — BanglaASR

শুধু বাংলা অডিও/ভিডিও থেকে সাবটাইটেল বানানোর Streamlit অ্যাপ।
Bengali-only subtitle app — upload Bengali audio or video, get subtitles (SRT / VTT) and plain text.

## মডেল / Model

- **BanglaASR** (`bangla-speech-processing/BanglaASR`) — Whisper-small, Mozilla Common Voice বাংলায় fine-tuned।
- এই অ্যাপে ব্যবহৃত ফরম্যাট: CTranslate2 int8 (`muhammadantor/typly-banglaasr-ct2`, 238 MB) — faster-whisper দিয়ে চলে, রানটাইমে Hugging Face hub থেকে ডাউনলোড হয়।

## জেনে রাখুন / Know this first

- **ভালো দিক:** বাংলা বানান Whisper large-v3-turbo-র চেয়ে ভালো (যেমন: বাংলাদেশিকে, যদি, ঢাকায়, পরমাণুর, ভূমিকম্পের — সব ঠিক)।
- **খারাপ দিক:** লম্বা অডিওতে মাঝখানের কিছু কথা বাদ পড়তে পারে। ৫৫ সেকেন্ডের পরীক্ষায় মাঝের ~২০ সেকেন্ড আর শেষের অংশ আসেনি, আর সাবটাইটেল মাত্র ২টা বড় টুকরো (৩০ সেকেন্ড করে) হয়েছিল।
- তাই ছোট অডিওতে (১–২ মিনিট) এই অ্যাপ ভালো; লম্বা অডিওতে Whisper turbo-র অ্যাপ বেশি সম্পূর্ণ লেখা দেয়।

## মাপা ফল / Measured (55 s Bengali voice note, this VM)

| | BanglaASR (int8) | Whisper large-v3-turbo (int8) |
|---|---|---|
| সময় (RTF) | 20 s (0.37×) | 110 s (1.99×) |
| RAM (peak) | ~783 MB | ~1.65 GB |
| মডেল | 238 MB | ~1.6 GB |
| সেগমেন্ট | 2 (30 s / 24 s) | 8 (~4–7 s) |
| বানান | ভালো | ঘন ঘন ভুল |
| কথা বাদ পড়া | মাঝের ~২০ সেকেন্ড + শেষাংশ | প্রায় নেই |

## চালানো / Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

ffmpeg দরকার (packages.txt-এ আছে — Streamlit Cloud নিজে বসিয়ে নেয়)।
