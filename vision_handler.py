#!/usr/bin/env python3
"""
Vision Handler for Jarvis - Qwen2.5-VL Integration
Handles model loading, screen capture, and JSON-enforced generation.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import torch
    from PIL import Image
    from airllm import AutoModel
    from transformers import AutoProcessor
    import mss
    import mss.tools
except ImportError as e:
    logging.error(f"Missing dependency in vision_handler: {e}")
    raise


logger = logging.getLogger("Jarvis.Vision")


class VisionHandlerError(Exception):
    """Custom exception for vision handler errors."""
    pass


class VisionHandler:
    """Handles vision model operations for screen understanding."""

    def __init__(
        self,
        model_path: str,
        max_tokens: int = 512,
        temperature: float = 0.2
    ):
        """
        Initialize the vision handler.
        
        Args:
            model_path: Local path to the model directory
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        self.model_path = Path(model_path)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model = None
        self.processor = None
        
        if not self.model_path.exists():
            raise VisionHandlerError(f"Model path does not exist: {model_path}")
        
        self._load_model()

    def _load_model(self):
        """Load the Qwen2.5-VL model and processor."""
        logger.info(f"Loading model from {self.model_path}...")
        
        try:
            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            
            # Load model with AirLLM for optimized inference
            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                auto_device_map="cuda",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            
            logger.info("Model loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise VisionHandlerError(f"Model loading failed: {e}")

    def capture_screen(self) -> Image.Image:
        """
        Capture current screen and resize to max dimensions.
        
        Returns:
            PIL Image of the screen
        """
        try:
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[0]  # Full virtual screen
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes(
                    "RGB",
                    screenshot.size,
                    screenshot.bgra,
                    "raw",
                    "BGRX"
                )
                
                # Resize if needed (maintain aspect ratio)
                max_size = 1024
                width, height = img.size
                
                if width > max_size or height > max_size:
                    ratio = min(max_size / width, max_size / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                return img
                
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            raise VisionHandlerError(f"Screen capture failed: {e}")

    def _parse_json_response(self, text: str, retries: int = 2) -> Dict[str, Any]:
        """
        Parse JSON from LLM response with regex cleanup and retry logic.
        
        Args:
            text: Raw LLM response text
            retries: Number of retry attempts on parse failure
            
        Returns:
            Parsed JSON dict
            
        Raises:
            VisionHandlerError: If parsing fails after retries
        """
        original_text = text
        
        for attempt in range(retries + 1):
            try:
                # Try direct parse first
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            
            # Regex to extract JSON object
            json_pattern = r'\{[^{}]*\}(?=\s*(?:,|\]|$))'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            if matches:
                # Try the largest/most complete match
                for match in reversed(matches):
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            # Try to find JSON between ```json markers
            markdown_pattern = r'```(?:json)?\s*({.*?})\s*```'
            markdown_matches = re.findall(markdown_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if markdown_matches:
                try:
                    return json.loads(markdown_matches[0])
                except json.JSONDecodeError:
                    pass
            
            # If we have retries left, raise to trigger retry in caller
            if attempt < retries:
                logger.warning(f"JSON parse attempt {attempt + 1} failed, will retry...")
                raise json.JSONDecodeError("Parse failed", text, 0)
        
        # All attempts failed
        logger.error(f"Failed to parse JSON after {retries + 1} attempts. Raw text: {original_text[:200]}...")
        raise VisionHandlerError("Failed to parse JSON response from LLM")

    def prompt(self, user_input: str, screenshot: bool = True) -> Dict[str, Any]:
        """
        Send a prompt to the vision model with optional screenshot.
        
        Args:
            user_input: User's text command
            screenshot: Whether to capture and include screen image
            
        Returns:
            Parsed JSON response dict
        """
        if self.model is None or self.processor is None:
            raise VisionHandlerError("Model not initialized")
        
        # System prompt enforcing strict JSON output
        system_prompt = (
            "You are Jarvis, a Windows desktop assistant with vision capabilities. "
            "You can see the user's screen and control their computer. "
            "You MUST respond with ONLY a valid JSON object, no other text. "
            "The JSON must have this exact structure:\n"
            '{"action": "<action_name>", "target": "<optional_target>", "args": {<key_value_pairs>}}\n'
            "or for text responses:\n"
            '{"action": "respond_text", "text": "<your_message>"}\n'
            "\nSupported actions:\n"
            "- launch_app: {\"name\": \"app_name\"}\n"
            "- open_url: {\"url\": \"https://...\"}\n"
            "- search_web: {\"query\": \"search terms\"}\n"
            "- type_text: {\"text\": \"text to type\"}\n"
            "- click_position: {\"x\": int, \"y\": int}\n"
            "- move_mouse: {\"x\": int, \"y\": int}\n"
            "- scroll: {\"amount\": int}\n"
            "- press_hotkey: {\"keys\": [\"ctrl\", \"c\"]}\n"
            "- get_system_info: {}\n"
            "- respond_text: {\"text\": \"message\"}\n"
            "\nAnalyze the screen image and user command. Decide the best action. "
            "Output ONLY the JSON object. No markdown, no explanations."
        )
        
        # Prepare inputs
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add user message with image if screenshot enabled
        if screenshot:
            try:
                screen_image = self.capture_screen()
                user_content = [
                    {"type": "image", "image": screen_image},
                    {"type": "text", "text": f"User command: {user_input}"}
                ]
                messages.append({"role": "user", "content": user_content})
            except VisionHandlerError as e:
                logger.warning(f"Screenshot failed, using text-only: {e}")
                messages.append({"role": "user", "content": user_input})
        else:
            messages.append({"role": "user", "content": user_input})
        
        try:
            # Process inputs through the processor
            inputs = self.processor(
                text=[msg["content"] if isinstance(msg["content"], str) else msg["content"][-1]["text"] 
                      for msg in messages if msg["role"] != "system"],
                images=[screen_image] if screenshot and 'screen_image' in dir() else None,
                return_tensors="pt",
                padding=True
            )
            
            # Move to GPU
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") if hasattr(v, "to") else v for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=self.temperature > 0,
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )
            
            # Decode response
            response_text = self.processor.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # Clean up response (remove input echo if present)
            if user_input in response_text:
                response_text = response_text.split(user_input)[-1].strip()
            
            logger.debug(f"Raw LLM response: {response_text[:200]}")
            
            # Parse JSON
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise VisionHandlerError(f"LLM generation failed: {e}")
