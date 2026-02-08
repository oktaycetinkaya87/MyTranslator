# MyTranslator 🚀

**MyTranslator** is a high-performance, native macOS translation utility designed for academic and professional use. It bridges the gap between your clipboard and advanced AI translation, offering instant, context-aware translations and human-level text refinement.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

## ✨ Key Features

### ⚡️ Ultra-Low Latency with Gemini 2.5 Flash-Lite

Powered by Google's latest **Gemini 2.5 Flash-Lite** model, MyTranslator is optimized for speed.

- **Instant Response:** Designed for sub-second query processing.
- **Smart Warmup:** Automatically establishes SSL/TLS tunnels upon launch to eliminate "cold start" latency.
- **Heartbeat System:** Keeps the connection alive in the background to ensure the API is always ready when you are.

### ⌨️ Seamless "Double Copy" Trigger (Cmd+C+C)

Forget switching apps. Just highlight text and press `Cmd+C` twice.

- **Background Listening:** A lightweight background thread monitors keyboard events using `pynput`.
- **Smart Activation:** Detects the double-press pattern within a 0.5s window and instantly launches the translation popup.

### 🍎 Native macOS Integration (AppKit)

Built specifically for macOS, leveraging native APIs for maximum stability and performance.

- **Thread-Safe Clipboard:** Uses `NSPasteboard` (via `pyobjc`) instead of subprocess calls, making clipboard reading **10x faster** and crash-proof.
- **Focus Management:** Uses native `NSApplication` calls to steal focus instantly, bypassing OS restrictions that often plague Python apps.
- **Agent Mode:** Runs silently in the background, hidden from the Dock and App Switcher, keeping your workspace clean.

### 🎓 Academic "Humanize" Mode

Go beyond translation. The **Humanize** feature rewrites your text to sound more natural and academic, specifically designed to bypass AI detection filters.

- **High Perplexity & Burstiness:** Varied sentence structures and vocabulary usage to mimic human writing styles.
- **Context Preservation:** Maintains 100% of the original academic meaning while enhancing flow and readability.

## 🛠 Technical Architecture

- **Core:** Python 3.12+
- **GUI:** PyQt6 (Modern, responsive, and customizable)
- **Input Monitoring:** `pynput` (Global keyboard hook)
- **Clipboard/System:** `pyobjc-framework-Cocoa` (AppKit integration)
- **AI Engine:** `google-genai` SDK (Gemini 2.5 Flash-Lite)

## 🚀 Installation & Usage

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/yourusername/MyTranslator.git
    cd MyTranslator
    ```

2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set API Key:**
    Create a `.env` file in the root directory:

    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    ```

4. **Run:**

    ```bash
    python main.py
    ```

5. **Usage:**
    - Highlight any text in any app.
    - Press `Cmd + C` twice quickly.
    - The MyTranslator popup will appear with the translation.
    - Click the **✨** button to humanize the text.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
