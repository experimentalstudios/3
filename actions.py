#!/usr/bin/env python3
"""
Action Handlers for Jarvis - Windows Desktop Control
Provides functions for launching apps, web search, mouse/keyboard control, and system info.
"""

import os
import sys
import logging
import subprocess
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import pyautogui
    import keyboard
    import psutil
    from duckduckgo_search import DDGS
    import win32com.client
except ImportError as e:
    logging.error(f"Missing dependency in actions: {e}")
    raise


logger = logging.getLogger("Jarvis.Actions")

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class ActionHandler:
    """Handles all desktop action executions."""

    def __init__(self):
        """Initialize the action handler."""
        self.shell = win32com.client.Dispatch("WScript.Shell")

    def _safe_result(self, success: bool, message: str) -> Dict[str, Any]:
        """Create a standardized result dictionary."""
        return {
            "status": "success" if success else "error",
            "message": message
        }

    def launch_app(self, name: str) -> Dict[str, Any]:
        """
        Launch an application by name.
        
        Args:
            name: Application name (e.g., "chrome", "notepad", "excel")
            
        Returns:
            Result dict with status and message
        """
        if not name:
            return self._safe_result(False, "No application name provided")
        
        name_lower = name.lower().strip()
        
        # Common app mappings
        app_mappings = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "excel": "excel.exe",
            "microsoft excel": "excel.exe",
            "word": "winword.exe",
            "microsoft word": "winword.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "vscode": "Code.exe",
            "visual studio code": "Code.exe",
            "terminal": "wt.exe",
            "windows terminal": "wt.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
        }
        
        exe_name = app_mappings.get(name_lower, f"{name_lower}.exe")
        
        try:
            # Try to start the application
            subprocess.Popen(
                exe_name,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Launched application: {name}")
            return self._safe_result(True, f"Opened {name}")
        except FileNotFoundError:
            # Try searching in PATH
            exe_path = shutil.which(exe_name)
            if exe_path:
                try:
                    subprocess.Popen(
                        exe_path,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    logger.info(f"Launched application: {name} from {exe_path}")
                    return self._safe_result(True, f"Opened {name}")
                except Exception as e:
                    logger.error(f"Failed to launch {name}: {e}")
                    return self._safe_result(False, f"Could not open {name}")
            
            # Try common installation paths for Windows
            common_paths = [
                Path(r"C:\Program Files"),
                Path(r"C:\Program Files (x86)"),
                Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local")),
            ]
            
            for base_path in common_paths:
                if not base_path.exists():
                    continue
                    
                # Search for the executable
                try:
                    for exe_file in base_path.rglob(exe_name):
                        if exe_file.is_file():
                            subprocess.Popen(
                                str(exe_file),
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            logger.info(f"Launched application: {name} from {exe_file}")
                            return self._safe_result(True, f"Opened {name}")
                except PermissionError:
                    continue
            
            return self._safe_result(False, f"Application '{name}' not found")
            
        except Exception as e:
            logger.error(f"Error launching {name}: {e}")
            return self._safe_result(False, f"Error opening {name}: {str(e)}")

    def open_url(self, url: str) -> Dict[str, Any]:
        """
        Open a URL in the default browser.
        
        Args:
            url: The URL to open
            
        Returns:
            Result dict
        """
        if not url:
            return self._safe_result(False, "No URL provided")
        
        # Ensure URL has protocol
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        try:
            os.startfile(url)
            logger.info(f"Opened URL: {url}")
            return self._safe_result(True, f"Opened {url}")
        except Exception as e:
            logger.error(f"Failed to open URL: {e}")
            return self._safe_result(False, f"Could not open URL: {str(e)}")

    def search_web(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search using DuckDuckGo.
        
        Args:
            query: Search query string
            
        Returns:
            Result dict with top results
        """
        if not query:
            return self._safe_result(False, "No search query provided")
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                
            if not results:
                return self._safe_result(False, "No search results found")
            
            # Format results
            result_summary = "\n".join([f"- {r['title']}: {r['href']}" for r in results[:3]])
            message = f"Top results for '{query}':\n{result_summary}"
            
            logger.info(f"Search completed for: {query}")
            return self._safe_result(True, message)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._safe_result(False, f"Search failed: {str(e)}")

    def click_position(self, x: int, y: int) -> Dict[str, Any]:
        """
        Click at specific screen coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Result dict
        """
        try:
            screen_width, screen_height = pyautogui.size()
            
            # Validate coordinates
            if not (0 <= x <= screen_width) or not (0 <= y <= screen_height):
                return self._safe_result(
                    False, 
                    f"Coordinates ({x}, {y}) out of bounds. Screen size: {screen_width}x{screen_height}"
                )
            
            pyautogui.click(x, y)
            logger.info(f"Clicked at position: ({x}, {y})")
            return self._safe_result(True, f"Clicked at ({x}, {y})")
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return self._safe_result(False, f"Click failed: {str(e)}")

    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """
        Move mouse to specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Result dict
        """
        try:
            screen_width, screen_height = pyautogui.size()
            
            if not (0 <= x <= screen_width) or not (0 <= y <= screen_height):
                return self._safe_result(
                    False,
                    f"Coordinates ({x}, {y}) out of bounds"
                )
            
            pyautogui.moveTo(x, y, duration=0.5)
            logger.info(f"Moved mouse to: ({x}, {y})")
            return self._safe_result(True, f"Moved mouse to ({x}, {y})")
            
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return self._safe_result(False, f"Mouse move failed: {str(e)}")

    def scroll(self, amount: int) -> Dict[str, Any]:
        """
        Scroll up or down.
        
        Args:
            amount: Scroll amount (positive = up, negative = down)
            
        Returns:
            Result dict
        """
        try:
            pyautogui.scroll(amount)
            direction = "up" if amount > 0 else "down"
            logger.info(f"Scrolled {direction} by {abs(amount)}")
            return self._safe_result(True, f"Scrolled {direction}")
            
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return self._safe_result(False, f"Scroll failed: {str(e)}")

    def type_text(self, text: str) -> Dict[str, Any]:
        """
        Type text at current cursor position.
        
        Args:
            text: Text to type
            
        Returns:
            Result dict
        """
        if not text:
            return self._safe_result(False, "No text provided")
        
        try:
            pyautogui.write(text, interval=0.02)
            logger.info(f"Typed text: {text[:50]}...")
            return self._safe_result(True, f"Typed: {text[:30]}..." if len(text) > 30 else f"Typed: {text}")
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return self._safe_result(False, f"Type failed: {str(e)}")

    def press_hotkey(self, keys: List[str]) -> Dict[str, Any]:
        """
        Press a keyboard hotkey combination.
        
        Args:
            keys: List of key names (e.g., ["ctrl", "c"])
            
        Returns:
            Result dict
        """
        if not keys:
            return self._safe_result(False, "No keys provided")
        
        try:
            # Use keyboard module for reliable hotkey execution
            if len(keys) == 1:
                keyboard.press_and_release(keys[0])
            else:
                keyboard.send("+".join(keys))
            
            key_str = "+".join(keys)
            logger.info(f"Pressed hotkey: {key_str}")
            return self._safe_result(True, f"Pressed {key_str}")
            
        except Exception as e:
            logger.error(f"Hotkey failed: {e}")
            return self._safe_result(False, f"Hotkey failed: {str(e)}")

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information (battery, RAM, CPU).
        
        Returns:
            Result dict with system stats
        """
        try:
            info = {}
            
            # Battery
            battery = psutil.sensors_battery()
            if battery:
                info["battery"] = f"{battery.percent}%"
                if battery.power_plugged:
                    info["battery"] += " (Charging)"
            else:
                info["battery"] = "N/A (Desktop)"
            
            # RAM
            ram = psutil.virtual_memory()
            info["ram"] = f"{ram.percent}% used ({ram.available / 1024**3:.1f}GB free)"
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            info["cpu"] = f"{cpu_percent}% usage"
            
            # Format message
            message = (
                f"System Info:\n"
                f"• Battery: {info['battery']}\n"
                f"• RAM: {info['ram']}\n"
                f"• CPU: {info['cpu']}"
            )
            
            logger.info("Retrieved system info")
            return self._safe_result(True, message)
            
        except Exception as e:
            logger.error(f"System info failed: {e}")
            return self._safe_result(False, f"System info failed: {str(e)}")

    def read_file(self, path: str) -> Dict[str, Any]:
        """
        Read contents of a file.
        
        Args:
            path: File path
            
        Returns:
            Result dict with file contents
        """
        if not path:
            return self._safe_result(False, "No file path provided")
        
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return self._safe_result(False, f"File not found: {path}")
            
            if not file_path.is_file():
                return self._safe_result(False, f"Not a file: {path}")
            
            content = file_path.read_text(encoding="utf-8")
            
            # Truncate long files
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            
            logger.info(f"Read file: {path}")
            return self._safe_result(True, f"Contents of {path}:\n{content}")
            
        except Exception as e:
            logger.error(f"Read file failed: {e}")
            return self._safe_result(False, f"Read failed: {str(e)}")

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            path: File path
            content: Content to write
            
        Returns:
            Result dict
        """
        if not path:
            return self._safe_result(False, "No file path provided")
        
        if content is None:
            return self._safe_result(False, "No content provided")
        
        try:
            file_path = Path(path).expanduser()
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Wrote file: {path}")
            return self._safe_result(True, f"Written to {path}")
            
        except Exception as e:
            logger.error(f"Write file failed: {e}")
            return self._safe_result(False, f"Write failed: {str(e)}")

    def execute_shell(self, command: str) -> Dict[str, Any]:
        """
        Execute a shell command.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Result dict with output
        """
        if not command:
            return self._safe_result(False, "No command provided")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout or result.stderr or "Command executed (no output)"
            
            # Truncate long output
            if len(output) > 2000:
                output = output[:2000] + "\n... (truncated)"
            
            status = result.returncode == 0
            logger.info(f"Executed shell: {command}")
            return self._safe_result(status, output.strip())
            
        except subprocess.TimeoutExpired:
            return self._safe_result(False, "Command timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Shell execution failed: {e}")
            return self._safe_result(False, f"Execution failed: {str(e)}")
