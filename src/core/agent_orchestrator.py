import re
import threading
from src.core.ollama_client import OllamaClient
from src.core.agents import get_planner_prompt, get_coder_prompt, get_reviewer_prompt

class AgentOrchestrator:
    def __init__(self, ollama_client=None, ide_ref=None):
        self.ollama = ollama_client or OllamaClient()
        self.ide_ref = ide_ref
        self.is_running = False

    def run_autonomous_loop(self, task, context, callback):
        """Executes the Planner -> Coder -> Reviewer loop."""
        self.is_running = True
        
        def loop():
            try:
                # 1. Planning
                callback("\n[PHASE 1/3] 🧠 ARCHITECTING SOLUTION...", "sys")
                plan_prompt = get_planner_prompt(task, context)
                # Use fast_model for planning if it's a simple navigation-style task
                model = self.ollama.fast_model if "[[EXPAND" in task or "[[OPEN" in task else self.ollama.coder_model
                plan = self.ollama.run(model, "You are a Senior Architect.", plan_prompt)
                callback(f"\n--- BLUEPRINT GENERATED ---\n{plan}\n", "bot")
                self.execute_actions(plan, callback)

                # FAST TRACK: If the plan only contains UI actions (EXPAND, COLLAPSE, OPEN) 
                # and NO code block actions, skip Phase 2 and 3.
                ui_actions = re.findall(r"\[\[(OPEN_FILE|EXPAND_FOLDER|COLLAPSE_FOLDER):\s*.*?\]\]", plan)
                code_actions = re.findall(r"\[\[(CREATE_FILE|UPDATE_FILE|DELETE_FILE):\s*.*?\]\]", plan)
                
                if ui_actions and not code_actions:
                    callback("\n✨ UI NAVIGATION COMPLETED.", "sys")
                    return

                # 2. Coding
                if not self.is_running: return
                callback("\n[PHASE 2/3] 💻 CONSTRUCTING CODE (Qwen 2.5 Coder)...", "sys")
                code_prompt = get_coder_prompt(plan, context)
                code = self.ollama.run(self.ollama.coder_model, "You are a Senior Engineer.", code_prompt)
                callback(f"\n--- IMPLEMENTATION COMPLETE ---\n{code}\n", "bot")
                self.execute_actions(code, callback)

                # 3. Review
                if not self.is_running: return
                callback("\n[PHASE 3/3] 🔍 QUALITY ASSURANCE REVIEW (Qwen 3)...", "sys")
                review_prompt = get_reviewer_prompt(code, context)
                review = self.ollama.run(self.ollama.reviewer_model, "You are a Perfectionist Reviewer.", review_prompt)
                callback(f"\n--- REVIEW INSIGHTS ---\n{review}\n", "bot")
                self.execute_actions(review, callback)

                callback("\n✨ AUTONOMOUS MISSION SUCCESSFUL.", "sys")
            except Exception as e:
                callback(f"\n❌ Loop Error: {str(e)}", "sys")
            finally:
                self.is_running = False
                callback(None, "done")

        threading.Thread(target=loop, daemon=True).start()

    def execute_actions(self, text, callback=None):
        """Parses [[ACTION: path]] and content from text and executes on IDE."""
        if not self.ide_ref: return

        # Pattern: [[ACTION_TYPE: path]] \n ```language \n content \n ```
        # Also handle actions without code blocks (OPEN, DELETE, EXPAND, COLLAPSE)
        
        # 1. Simple actions: OPEN, DELETE, EXPAND, COLLAPSE, RUN, LIST, GLOB, GREP, FETCH, SEARCH, mission, sub_agent, bulk open, aider
        simple_actions = re.findall(r"\[\[(OPEN_FILE|DELETE_FILE|EXPAND_FOLDER|COLLAPSE_FOLDER|RUN_COMMAND|LIST_FILES|GLOB_SEARCH|GREP_SEARCH|WEB_FETCH|WEB_SEARCH|TODO_READ|TODO_WRITE|SUB_AGENT|OPEN_FOLDER_FILES|AIDER_TASK):\s*(.*?)\]\]", text)
        for action, path in simple_actions:
            success = self.ide_ref.apply_agent_action(action, path.strip())
            if success and callback:
                callback(f"🤖 Agent: {action} {path.strip()}", "sys")

        # 2. Complex actions: CREATE, UPDATE
        complex_pattern = r"\[\[(CREATE_FILE|UPDATE_FILE):\s*(.*?)\]\]\s*```.*?\n(.*?)\n```"
        complex_actions = re.findall(complex_pattern, text, re.DOTALL)
        
        for action, path, content in complex_actions:
            success = self.ide_ref.apply_agent_action(action, path.strip(), content)
            if success and callback:
                callback(f"🤖 Agent: {action} {path.strip()}", "sys")

    def stop(self):
        self.is_running = False
        self.ollama.stop()
