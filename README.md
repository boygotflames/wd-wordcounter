# 🔤 WD Word Counter

![WD Icon](assets/wd_pixel.png)

A **privacy-first desktop word counter** with a clean black “terminal” aesthetic and a **Rust-accelerated backend** (with Python fallback).  
No tracking. No telemetry. Works fully offline.

## ✨ Features

- **Real-time counting**: words, characters (with/without spaces), sentences, paragraphs
- **Word frequency + visualization** (heatmap / visual breakdowns)
- **Readability scoring** (powered by `textstat`)
- **Exports**: JSON, CSV, HTML, Markdown, TXT
- **Offline by design** (no network needed)
- **Optional Rust backend** for faster counting (falls back to Python if Rust build isn’t available)

## 📥 Installation

### Windows (recommended)
- Download the latest **portable** `Word-Counter.exe` from **Releases**:
  - https://github.com/boygoflames/wd-wordcounter/releases
- Double-click → app opens. No terminal.

> Tip: If you later publish an installer, you’ll also find it in Releases.

### From source (Windows / Linux / macOS)
```bash
git clone https://github.com/boygoflames/wd-wordcounter.git
cd wd-wordcounter
pip install -r requirements.txt
python WD.py