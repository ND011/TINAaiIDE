import requests
import json
import threading
import subprocess
import time
import os
import sys

class OllamaClient:
    def __init__(self, chat_model="llama3.2:3b", coder_model="qwen2.5-coder:7b", reviewer_model="llama3.2:3b", fast_model="qwen2.5-coder:1.5b"):
        self.chat_model = chat_model
        self.coder_model = coder_model
        self.reviewer_model = reviewer_model
        self.fast_model = fast_model
        self.api_base = "http://localhost:11434/api/generate"
        self.stop_event = threading.Event()
        self.default_options = {"num_ctx": 4096, "num_thread": 4, "temperature": 0.7}

    def check_connection(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except: return False

    def get_available_models(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
        except: pass
        return []

    def classify_intent(self, user_input):
        """Dynamic Router: SPEC, EXECUTE, or HYBRID."""
        prompt = f"""
        Classify the user request into one of:
        - SPEC (planning/design only)
        - EXECUTE (direct small action like "run this" or "delete that")
        - HYBRID (planning followed by immediate implementation)

        Return ONLY a JSON object: {{ "mode": "SPEC | EXECUTE | HYBRID" }}
        Input: {user_input}
        """
        try:
            res = self.run(self.fast_model, "You are a JSON router.", prompt)
            # Find JSON in response
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return data.get("mode", "HYBRID").upper()
        except: pass
        return "HYBRID" # Default

    def stream_run(self, model_name, system_prompt, user_prompt, callback, options=None):
        self.stop_event.clear()
        payload = {"model": model_name, "system": system_prompt, "prompt": user_prompt, "stream": True, "options": options or self.default_options}
        def run_api():
            try:
                response = requests.post(self.api_base, json=payload, stream=True, timeout=120)
                for line in response.iter_lines():
                    if self.stop_event.is_set(): break
                    if line:
                        chunk = json.loads(line)
                        if "response" in chunk: callback(chunk["response"])
                        if chunk.get("done", False): break
            except Exception as e: callback(f"\n[Error]: {str(e)}")
            finally: callback(None)
        threading.Thread(target=run_api, daemon=True).start()

    def run(self, model_name, system_prompt, user_prompt, options=None):
        payload = {"model": model_name, "system": system_prompt, "prompt": user_prompt, "stream": False, "options": options or self.default_options}
        try:
            response = requests.post(self.api_base, json=payload, timeout=300)
            return response.json().get("response", "")
        except Exception as e: return f"Error: {str(e)}"

    def stop(self): self.stop_event.set()
import re
