import requests
import json
import threading

class OllamaClient:
    def __init__(self, chat_model="llama3.2:latest", coder_model="qwen2.5-coder:7b", reviewer_model="qwen3:4b", fast_model="qwen2.5-coder:1.5b"):
        self.chat_model = chat_model
        self.coder_model = coder_model
        self.reviewer_model = reviewer_model
        self.fast_model = fast_model
        # Fallback to qwen3:4b if chat_model is missing, or llama3.2
        self.api_base = "http://localhost:11434/api/generate"
        self.stop_event = threading.Event()

    def check_connection(self):
        """Verifies if the Ollama server is reachable."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def stream_run(self, model_name, system_prompt, user_prompt, callback):
        """Executes ollama via HTTP /api/generate and streams output."""
        self.stop_event.clear()
        
        payload = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": True
        }

        def run_api():
            try:
                response = requests.post(self.api_base, json=payload, stream=True, timeout=60)
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if self.stop_event.is_set():
                        break
                        
                    if line:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            callback(chunk["response"])
                        if chunk.get("done", False):
                            break
                
            except Exception as e:
                callback(f"\n[Error]: {str(e)}")
            finally:
                callback(None) # Signal completion

        threading.Thread(target=run_api, daemon=True).start()

    def stop(self):
        self.stop_event.set()

    def classify_intent(self, query):
        """Fast check to see if user wants to build/fix code vs talk."""
        system = """You are an intent classifier. Respond with ONLY 'AUTO' or 'CHAT'.
        
EXAMPLES:
- "open shree folder" -> AUTO
- "open it" -> AUTO
- "create a hello world script" -> AUTO
- "expand src directory" -> AUTO
- "create a folder named dv" -> AUTO
- "build a website for my routine" -> AUTO
- "tell me a joke" -> CHAT
- "what is python?" -> CHAT
- "how do I use the explorer?" -> CHAT

Respond with 'AUTO' for any command that requires the IDE to DO something (navigate, create, edit, run). 
Respond with 'CHAT' for general conversation or explanations.
NO OTHER WORDS."""
        result = self.run(self.fast_model, system, query)
        return "AUTO" if "AUTO" in result.upper() else "CHAT"

    def run(self, model_name, system_prompt, user_prompt):
        """Synchronous version for internal tasks."""
        payload = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False
        }
        try:
            response = requests.post(self.api_base, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            return f"Error: {str(e)}"
