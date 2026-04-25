# screen-agent

> ReAct-based autonomous computer agent — screenshot → LLM → action loop.

Powered by **Gemma 3 12B** via **Ollama**. The agent observes the screen, reasons about what to do, and executes mouse/keyboard actions — no DOM access, no accessibility trees, no external APIs.

---

## How It Works

The agent runs a continuous **Perceive → Reason → Act** loop:

```
Screenshot → Base64 Encode → LLM (Gemma 3 12B) → JSON Action → Executor → Next Screenshot
```

1. Captures a full-screen screenshot
2. Encodes it as Base64 and sends it to the LLM
3. LLM analyzes the raw image and outputs a structured action (click, type, scroll, etc.)
4. Executor performs the action via `pyautogui` / `pywinauto`
5. New screenshot is captured and the loop continues

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Request                     │
└────────────────────────┬────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │ Planner  │  (LLM - Gemma 3 12B)
                    └────┬─────┘
                         │
              ┌──────────▼──────────┐
              │    Vision Layer     │
              │                     │
              │  Current:           │
              │  Raw screenshot     │
              │                     │
              │  Planned:           │
              │  YOLOv11 + OCR      │
              │  Object ID map      │
              └──────────┬──────────┘
                         │
                    ┌────▼─────┐
                    │ Executor │  pyautogui / pywinauto
                    └────┬─────┘
                         │
                  ┌──────▼───────┐
                  │  Windows OS  │
                  └──────┬───────┘
                         │ feedback screenshot
                         └──────────────────────────┐
                                                    │
                                               loops back
```

---

## Vision Pipeline

### Current: Raw Screenshot

The active pipeline sends the full screenshot directly to the LLM with no preprocessing:

```json
{
  "model": "gemma3:12b",
  "images": ["<base64-encoded-screenshot>"],
  "prompt": "..."
}
```

The LLM infers UI elements from raw pixels and returns a JSON action:

```json
{ "action": "click", "x": 412, "y": 230 }
{ "action": "type", "text": "Hello World" }
```

Simple, but accuracy is gated entirely on the model's vision capability.

### Planned: YOLOv11 + OCR

A structured perception layer is in development. The planned flow:

1. Screenshot passes through **YOLOv11** — detects UI elements (buttons, inputs, icons, etc.) and assigns each a unique ID
2. **OCR** optionally extracts visible text with bounding boxes
3. YOLOv11 overlays IDs on the screenshot
4. LLM receives the annotated screenshot and references elements by ID
5. Executor maps the ID → exact bounding box → performs the action

Expected output format:

```json
{
  "objects": [
    { "id": 1, "label": "button", "bbox": [120, 45, 200, 75] },
    { "id": 2, "label": "input",  "bbox": [250, 45, 500, 75] }
  ],
  "texts": [
    { "text": "Search", "bbox": [130, 50, 195, 70] }
  ]
}
```

Benefits over raw screenshot: deterministic targeting, 95%+ detection accuracy, less hallucination, resolution-independent.

---

## Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10 / 11 (64-bit) |
| Python | 3.13+ |
| GPU | NVIDIA ≥ 8GB VRAM (recommended) |
| RAM | 16GB minimum |
| Ollama | Gemma 3 12B pulled locally |
| CPU-only | Supported, but noticeably slower |

> Tesseract OCR and a YOLO model are only required once the planned vision parser is integrated.

---

## Installation

```bash
# Clone
git clone https://github.com/yourusername/screen-agent.git
cd screen-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull the LLM
ollama pull gemma3:12b
```

---

## Usage

```bash
python mainwindow.py
```

Example prompts:

```
Open Notepad and write "Hello World".
Open Chrome, search for GitHub, and click the first result.
Open Task Manager and sort processes by CPU usage.
```

---

## Configuration

Edit `configs/agent.yaml` to adjust:

```yaml
model: gemma3:12b
temperature: 0.2
system: "You are a computer agent..."
```

---

## Roadmap

- [x] Raw screenshot → LLM → action loop
- [x] PyQt5 real-time observation UI
- [ ] YOLOv11 vision parser integration
- [ ] Object ID → bounding box executor system
- [ ] OCR text extraction layer
- [ ] Memory summarization across steps
- [ ] 4-bit quantization (target: ~2s/step latency)
- [ ] Linux support

---

## Tech Stack

- **Python 3.13**
- **Ollama** — local LLM inference
- **Gemma 3 12B** — vision + reasoning
- **pyautogui** — mouse/keyboard control
- **pywinauto** — Windows UI automation
- **PyQt5** — observation interface
- **YOLOv11** *(planned)* — UI element detection
- **Tesseract OCR** *(planned)* — text extraction

---

## License

MIT License. See [`LICENSE`](LICENSE) for details.