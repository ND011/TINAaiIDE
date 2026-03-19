import re
import threading
import os
import json
from src.core.ollama_client import OllamaClient
from src.core.agents import get_planner_prompt, get_coder_prompt, get_reviewer_prompt

class AgentOrchestrator:
    def __init__(self, ollama_client=None, ide_ref=None):
        self.ollama = ollama_client or OllamaClient()
        self.ide_ref = ide_ref
        self.is_running = False

    def run_autonomous_loop(self, task, context, callback):
        self.is_running = True
        
        def loop():
            try:
                # 1. INTENT ROUTER
                callback("\n[SYSTEM] 🧠 CLASSIFYING INTENT...", "sys")
                mode = self.ollama.classify_intent(task)
                callback(f" MODE: {mode}\n", "sys")

                if mode == "SPEC":
                    self.run_spec_mode(task, context, callback)
                elif mode == "EXECUTE":
                    self.run_execute_mode(task, context, callback)
                else: # HYBRID
                    self.run_hybrid_mode(task, context, callback)

            except Exception as e:
                callback(f"\n❌ Master Agent Error: {str(e)}", "sys")
            finally:
                self.is_running = False
                callback(None, "done")

        threading.Thread(target=loop, daemon=True).start()

    def run_spec_mode(self, task, context, callback):
        """Generates Requirements -> Design -> Tasks."""
        # 1. Requirements
        callback("\n[PHASE 1/3] 📝 GENERATING REQUIREMENTS...", "sys")
        req = self.ollama.run(self.ollama.chat_model, "Generate a requirements.md file.", f"Task: {task}\nContext: {context}")
        self.save_spec(task, "requirements.md", req)
        callback(f"\n--- REQUIREMENTS ---\n{req}\n", "bot")

        # 2. Design
        callback("\n[PHASE 2/3] 📐 ARCHITECTING DESIGN...", "sys")
        design = self.ollama.run(self.ollama.chat_model, "Generate a design.md file based on requirements.", req)
        self.save_spec(task, "design.md", design)
        callback(f"\n--- DESIGN ---\n{design}\n", "bot")

        # 3. Tasks
        callback("\n[PHASE 3/3] 📋 CREATING TASK LIST...", "sys")
        tasks = self.ollama.run(self.ollama.fast_model, "Generate a tasks.md checklist.", design)
        self.save_spec(task, "tasks.md", tasks)
        callback(f"\n--- TASKS ---\n{tasks}\n", "bot")
        callback("\n✨ SPECIFICATION COMPLETE. (Stored in /specs/)", "sys")

    def run_execute_mode(self, task, context, callback):
        """Direct tool execution for simple tasks."""
        callback("\n[FAST-TRACK] ⚡ EXECUTING DIRECT ACTION...", "sys")
        plan = self.ollama.run(self.ollama.fast_model, "You are an IDE controller. Output tools immediately.", get_planner_prompt(task, context))
        self.execute_actions(plan, callback)
        callback("\n✨ EXECUTION COMPLETE.", "sys")

    def run_hybrid_mode(self, task, context, callback):
        """Spec -> Execute Continuous Loop."""
        # 1. Spec
        callback("\n[HYBRID] 🧠 PHASE 1: PLANNING & SPEC...", "sys")
        plan = self.ollama.run(self.ollama.chat_model, "Generate execution plan.", get_planner_prompt(task, context))
        callback(f"\n--- BLUEPRINT ---\n{plan}\n", "bot")
        self.execute_actions(plan, callback)

        # 2. Continuous Execution
        if not self.is_running: return
        callback("\n[HYBRID] 💻 PHASE 2: IMPLEMENTATION...", "sys")
        code = self.ollama.run(self.ollama.coder_model, "Implement the plan.", get_coder_prompt(plan, context))
        callback(f"\n--- IMPLEMENTATION ---\n{code}\n", "bot")
        self.execute_actions(code, callback)

        # 3. Final Verification
        if not self.is_running: return
        callback("\n[HYBRID] 🔍 PHASE 3: VERIFICATION...", "sys")
        review = self.ollama.run(self.ollama.reviewer_model, "Review the code.", get_reviewer_prompt(code, context))
        self.execute_actions(review, callback)
        callback("\n✨ HYBRID MISSION SUCCESSFUL.", "sys")

    def save_spec(self, task, name, content):
        """Auto-save system for specs."""
        safe_task_name = re.sub(r'\W+', '_', task)[:30]
        spec_dir = os.path.join(os.getcwd(), "specs", safe_task_name)
        os.makedirs(spec_dir, exist_ok=True)
        with open(os.path.join(spec_dir, name), "w", encoding="utf-8") as f:
            f.write(content)

    def execute_actions(self, text, callback=None):
        if not self.ide_ref: return
        # Simple Actions
        mapping = {"Agent": "SUB_AGENT", "Bash": "RUN_COMMAND", "LS": "LIST_FILES", "Glob": "GLOB_SEARCH", "Grep": "GREP_SEARCH", "Read": "OPEN_FILE"}
        keys = "|".join(mapping.keys())
        simple_actions = re.findall(rf"\[\[({keys}):\s*(.*?)\]\]", text)
        for action_name, path in simple_actions:
            success = self.ide_ref.apply_agent_action(mapping.get(action_name), path.strip())
            if success and callback: callback(f"🤖 Master Agent: {action_name} {path.strip()}", "sys")

        # Complex Actions
        blocks = re.split(rf"\[\[(Write|Edit|MultiEdit):\s*(.*?)\]\]", text)
        for i in range(1, len(blocks), 3):
            action_name, path, content_after = blocks[i], blocks[i+1], blocks[i+2]
            internal_action = "CREATE_FILE" if action_name == "Write" else "UPDATE_FILE"
            code_match = re.search(r"```.*?\n(.*?)\n```", content_after, re.DOTALL)
            if code_match:
                success = self.ide_ref.apply_agent_action(internal_action, path.strip(), code_match.group(1))
                if success and callback: callback(f"🤖 Master Agent: {action_name} {path.strip()}", "sys")

    def stop(self): self.is_running = False; self.ollama.stop()
