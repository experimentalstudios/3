#!/usr/bin/env python3
"""
Jarvis Vision - Windows Desktop Assistant with Screen Understanding
Entry point with terminal UI, screen capture loop, and tool execution.
"""

import os
import sys
import json
import time
import logging
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List

# Third-party imports
try:
    from colorama import init as colorama_init, Fore, Style
    from rich.console import Console
    from rich.panel import Panel
    from rich.spinner import Spinner
    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
    from huggingface_hub import snapshot_download
except ImportError as e:
    print(f"Missing dependency: {e}. Please run 'pip install -r requirements.txt'")
    sys.exit(1)

# Local imports
from vision_handler import VisionHandler, VisionHandlerError
from actions import ActionHandler

# Initialize Colorama for Windows
colorama_init()

# Configure Logging
LOG_FILE = "jarvis.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Jarvis")

# Constants
CONFIG_PATH = Path("config.json")
MODEL_DIR = Path("models")
FULL_MODEL_PATH = MODEL_DIR / "Qwen2.5-VL-7B-Instruct"


class JarvisAssistant:
    """Main assistant class orchestrating UI, Vision, and Actions."""

    def __init__(self):
        self.console = Console()
        self.config: Dict[str, Any] = {}
        self.vision: Optional[VisionHandler] = None
        self.actions: ActionHandler = ActionHandler()
        self.running = True
        self.max_tool_iterations = 3

        # Load config
        if not CONFIG_PATH.exists():
            logger.error("config.json not found. Using defaults.")
            self.config = self._get_default_config()
        else:
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid config.json. Using defaults.")
                self.config = self._get_default_config()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "model_repo_id": "Qwen/Qwen2.5-VL-7B-Instruct",
            "local_model_dir": str(FULL_MODEL_PATH),
            "max_tokens": 512,
            "temperature": 0.2,
            "screenshot_quality": 85,
            "max_image_size": 1024,
            "log_level": "INFO"
        }

    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        self.console.print("\n[bold yellow]Interrupt received. Shutting down...[/bold yellow]")
        self.running = False

    def ensure_model_exists(self):
        """Download model if not present locally."""
        if FULL_MODEL_PATH.exists() and any(FULL_MODEL_PATH.iterdir()):
            self.console.print(f"[green]✓[/green] Model found at [cyan]{FULL_MODEL_PATH}[/cyan]")
            return

        self.console.print(Panel(
            "[bold yellow]Model not found locally.[/bold yellow]\n"
            f"Downloading [cyan]{self.config['model_repo_id']}[/cyan] to [cyan]{FULL_MODEL_PATH}[/cyan]\n"
            "This may take several minutes depending on your internet speed.",
            title="📥 Model Download",
            border_style="yellow"
        ))

        try:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Downloading model files...", total=None)
                
                snapshot_download(
                    repo_id=self.config["model_repo_id"],
                    local_dir=str(FULL_MODEL_PATH),
                    local_dir_use_symlinks=False,
                    ignore_patterns=["*.msgpack", "*.h5", "*.ot"]
                )
                progress.update(task, completed=100, total=100)
            
            self.console.print("[bold green]✓ Model download complete![/bold green]")
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            self.console.print(f"[bold red]✗ Error downloading model: {e}[/bold red]")
            self.console.print("Please check your internet connection and try again.")
            sys.exit(1)

    def initialize(self):
        """Initialize the vision handler."""
        self.ensure_model_exists()
        
        with self.console.status("[bold blue]Initializing AI Engine...", spinner="dots"):
            try:
                self.vision = VisionHandler(
                    model_path=str(FULL_MODEL_PATH),
                    max_tokens=self.config.get("max_tokens", 512),
                    temperature=self.config.get("temperature", 0.2)
                )
                self.console.print("[bold green]✓ AI Engine Ready[/bold green]")
            except Exception as e:
                logger.error(f"Initialization failed: {e}")
                self.console.print(f"[bold red]✗ Failed to initialize AI: {e}[/bold red]")
                sys.exit(1)

    def print_welcome(self):
        """Display welcome banner."""
        banner = Panel(
            "[bold cyan]Welcome to Jarvis - Your AI Desktop Assistant[/bold cyan]\n\n"
            "I can see your screen and control your computer.\n"
            "Type what you want me to do, or use commands:\n\n"
            "[yellow]/help[/yellow] - Show supported actions\n"
            "[yellow]/exit[/yellow] - Close Jarvis\n\n"
            "[dim]Examples:[/dim]\n"
            "• [green]'Open Chrome and search for pizza recipes'[/green]\n"
            "• [green]'What is my battery level?'[/green]\n"
            "• [green]'Click the start button'[/green]",
            title="🤖 Jarvis Vision",
            subtitle="Powered by Qwen2.5-VL",
            border_style="cyan"
        )
        self.console.print(banner)

    def print_help(self):
        """Display help menu."""
        help_text = (
            "[bold]Supported Actions:[/bold]\n\n"
            "[cyan]• open [app][/cyan]      - Launch applications (e.g., 'open chrome')\n"
            "[cyan]• search [query][/cyan]  - Google search (e.g., 'search python tutorials')\n"
            "[cyan]• type [text][/cyan]     - Type text anywhere\n"
            "[cyan]• click [x] [y][/cyan]   - Click at specific coordinates\n"
            "[cyan]• system info[/cyan]     - Show battery, RAM, CPU stats\n"
            "[cyan]• scroll[/cyan]          - Scroll up or down\n"
            "[cyan]• hotkey [keys][/cyan]   - Press keyboard shortcuts (e.g., 'hotkey ctrl c')\n\n"
            "[bold]Commands:[/bold]\n"
            "[yellow]/help, ?[/yellow] - Show this message\n"
            "[yellow]/exit, quit[/yellow] - Exit Jarvis"
        )
        self.console.print(Panel(help_text, title="Help", border_style="blue"))

    def parse_user_input(self, text: str) -> tuple[bool, str]:
        """
        Parse special commands. Returns (is_command, command_name).
        If not a command, returns (False, original_text).
        """
        cleaned = text.strip().lower()
        if cleaned in ["/help", "?"]:
            return True, "help"
        if cleaned in ["/exit", "quit", "exit"]:
            return True, "exit"
        return False, text

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool/action."""
        self.console.print(f"[dim]Executing: {tool_name}...[/dim]")
        
        try:
            if tool_name == "launch_app":
                return self.actions.launch_app(args.get("name", ""))
            elif tool_name == "open_url":
                return self.actions.open_url(args.get("url", ""))
            elif tool_name == "search_web":
                return self.actions.search_web(args.get("query", ""))
            elif tool_name == "type_text":
                return self.actions.type_text(args.get("text", ""))
            elif tool_name == "click_position":
                x = args.get("x", 0)
                y = args.get("y", 0)
                return self.actions.click_position(x, y)
            elif tool_name == "move_mouse":
                x = args.get("x", 0)
                y = args.get("y", 0)
                return self.actions.move_mouse(x, y)
            elif tool_name == "scroll":
                amount = args.get("amount", 0)
                return self.actions.scroll(amount)
            elif tool_name == "press_hotkey":
                keys = args.get("keys", [])
                return self.actions.press_hotkey(keys)
            elif tool_name == "get_system_info":
                return self.actions.get_system_info()
            elif tool_name == "respond_text":
                return {"status": "success", "message": args.get("text", "")}
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"status": "error", "message": str(e)}

    def process_request(self, user_input: str):
        """Process a single user request with potential tool loops."""
        iteration = 0
        
        while iteration < self.max_tool_iterations:
            iteration += 1
            
            # Call LLM (screen capture happens inside vision_handler.prompt)
            try:
                response = self.vision.prompt(user_input, screenshot=True)
            except VisionHandlerError as e:
                self.console.print(f"[red]AI Error: {e}[/red]")
                return
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")
                logger.exception("LLM Prompt failed")
                return

            # Check if response is a tool call or final answer
            action = response.get("action", "")
            args = response.get("args", {})

            if action == "respond_text":
                # Final text response
                msg = response.get("text", args.get("text", "Done."))
                self.console.print(f"[green]✓ {msg}[/green]")
                return
            
            if action:
                # Execute tool
                result = self.execute_tool(action, args)
                
                if result["status"] == "error":
                    self.console.print(f"[red]✗ {result['message']}[/red]")
                    user_input = f"The action '{action}' failed: {result['message']}. Please try again or explain the error."
                    continue
                
                if result.get("message"):
                    self.console.print(f"[green]✓ {result['message']}[/green]")
                
                # Feed result back to LLM for final natural language response
                feedback = f"Action '{action}' executed successfully. Result: {result.get('message', 'No details')}"
                user_input = f"{feedback}. Please confirm to the user what happened."
                continue
            
            # Fallback if no action found but JSON parsed
            self.console.print(f"[blue]ℹ {response}[/blue]")
            return

        self.console.print("[yellow]⚠ Max tool iterations reached.[/yellow]")

    def run(self):
        """Main execution loop."""
        # Change working directory to script directory for relative paths
        os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
        
        self.print_welcome()
        self.initialize()

        while self.running:
            try:
                # Get input
                self.console.print()
                user_input = input(f"{Fore.CYAN}🤖 What should I do? {Style.RESET_ALL}> ").strip()

                if not user_input:
                    continue

                # Check commands
                is_cmd, cmd = self.parse_user_input(user_input)
                if is_cmd:
                    if cmd == "help":
                        self.print_help()
                        continue
                    elif cmd == "exit":
                        self.console.print("[bold yellow]Goodbye! 👋[/bold yellow]")
                        self.running = False
                        continue

                # Process request
                self.console.print()
                with self.console.status("[bold blue]Thinking...", spinner="dots"):
                    self.process_request(user_input)

            except EOFError:
                self.running = False
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted.[/yellow]")
                self.running = False
            except Exception as e:
                logger.exception("Main loop error")
                self.console.print(f"[red]An unexpected error occurred: {e}[/red]")


def main():
    """Entry point."""
    app = JarvisAssistant()
    app.run()


if __name__ == "__main__":
    main()
