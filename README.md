# Jarvis Vision - AI Desktop Assistant

**100% Local. Windows-Only. Vision-Enabled.**

## Quick Start

1. **Double-click** `setup_and_run.bat`
2. Wait for the AI model to download (~15GB, may take several minutes)
3. Type commands like "Open Chrome" or "What's my battery level?"

## Supported Actions

| Command | Description | Example |
|---------|-------------|---------|
| `open [app]` | Launch applications | "open chrome", "open notepad" |
| `search [query]` | Web search via DuckDuckGo | "search python tutorials" |
| `type [text]` | Type text anywhere | "type hello world" |
| `click [x] [y]` | Click at coordinates | (AI determines from screen) |
| `system info` | Show battery, RAM, CPU | "what's my battery level?" |
| `scroll` | Scroll up/down | "scroll down" |
| `hotkey [keys]` | Press keyboard shortcuts | "press ctrl c" |

## Requirements

- **OS:** Windows 10/11 (64-bit)
- **Python:** 3.11 or higher
- **GPU:** NVIDIA with CUDA 12.x support
- **VRAM:** 16GB+ recommended (7B model with quantization)
- **Admin Rights:** Required for shell execution

## Architecture

- **Model:** Qwen2.5-VL-7B-Instruct (loaded locally into `./models/`)
- **Inference:** AirLLM with automatic CUDA device mapping
- **Screen Capture:** MSS library (fast, borderless)
- **Control:** pyautogui, keyboard, pywin32 for Windows automation
- **Search:** DuckDuckGo API (no key required)

## Self-Contained Design

- Model files live entirely in `./models/Qwen2.5-VL-7B-Instruct/`
- Virtual environment created in `./venv/`
- Running `uninstall.bat` removes ALL local data (venv + models)
- No cloud dependencies. No data leaves your machine.

## Manual Installation (Alternative)

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Troubleshooting

- **CUDA out of memory:** Close other GPU applications. The 7B model requires ~8GB VRAM with quantization.
- **Model download fails:** Check internet connection. Resume by re-running `setup_and_run.bat`.
- **App not found:** Ensure the application is installed and in PATH or Program Files.
- **Permission errors:** Run as Administrator for full shell execution capabilities.

## License

MIT License. For personal use only. Use responsibly.
