# 🤖 TINA AI COD: Professional Offline AI-Native IDE

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/ND011/TINAaiIDE)
[![Status](https://img.shields.io/badge/status-active-success.svg)](https://github.com/ND011/TINAaiIDE)
[![License](https://img.shields.io/badge/license-proprietary-red.svg)](https://github.com/ND011/TINAaiIDE)

## 🌟 The Vision

**TINA AI COD** is a world-class, 100% offline AI-native Integrated Development Environment (IDE). Designed for power users who demand professional-grade AI assistance (similar to Cursor or GitHub Copilot) without compromising on **privacy, security, or data sovereignty**.

Everything happens on your hardware. No cloud. No telemetry. No subscription. Just pure local intelligence.

---

## 🏗️ Technical Architecture

TINA AI COD is built on a multi-layered hybrid architecture that bridges high-level GUI interaction with low-level neural processing.

### 1. The Shell (GUI Layer)
- **Technology**: Built using Python and `CustomTkinter`.
- **Logic**: A sophisticated multi-panel layout managing the Activity Bar, Sidebar (Explorer/AI), Tabbed Editor, and Integrated Terminal.
- **Orchestration**: `src/gui/tina_ide.py` handles cross-component event coordination.

### 2. The Brain (Intelligence Layer)
- **LLM Orchestration**: Integrated with **Ollama** for seamless local model execution.
- **Agent Orchestrator**: Uses a `Planner → Coder → Reviewer` autonomous loop (`src/core/agent_orchestrator.py`) for executing complex coding tasks.
- **Expertise Modes**:
  - `Coder (7B)`: Deep logic and structural implementation.
  - `Chat (4B)`: High-speed conversational assistance.

### 3. Project Memory (RAG System)
- **Vector Database**: **ChromaDB**.
- **Embeddings**: `all-MiniLM-L6-v2` via **SentenceTransformers**.
- **Context Awareness**: TINA indexes your entire project, breaking code into overlapping chunks to ensure the AI "understands" the relationship between different modules.

---

## 🚀 Key Features

- **🌐 100% Offline RAG**: Ask questions about your entire codebase. The AI retrieves relevant snippets instantly using local vector search.
- **📟 Integrated Power Terminal**: Direct access to PowerShell/CMD within the IDE, with AI shortcuts for common tasks.
- **📂 Smart Explorer**: A filtered file system view that focuses on what matters, ignoring build artifacts and system noise.
- **🧠 AI Personas**: Specialized modes (CODER, AUDITOR, REFACTOR, DOCS) to tailor the AI's output to your current need.
- **🎨 Modern UI**: Premium dark mode design with syntax highlighting and smooth transitions.
- **🔌 Plugin Architecture**: Easily extend the IDE's functionality by dropping Python scripts into `src/plugins/`.

---

## 🛠️ Performance & Optimization

TINA AI COD is fine-tuned for high-performance workstations:
- **Target Specs**: Intel Core Ultra 9 / 32GB RAM / Intel Arc GPU.
- **Efficiency**: Designed to operate within a 10GB RAM envelope.
- **Concurrency**: Threaded AI interactions ensure the UI remains responsive during heavy LLM processing.

---

## 📂 System Manifest

| Module | Location | Description |
| :--- | :--- | :--- |
| **Main Entry** | `main.py` | Bootstraps the application. |
| **Logic Bridge** | `src/core/ollama_client.py` | Interfaces with the local LLM. |
| **Neural Search** | `src/core/rag.py` | Handles project indexing and retrieval. |
| **UI Components** | `src/ui/` | Individual components (Terminal, Sidebar, Editor). |
| **Legacy Archive** | `legacy/` | Archived prototypes and reference code (AI Editor, Agent Bridge). |

---

## 🛡️ Security & Privacy

Privacy isn't a feature; it's the foundation.
- **Zero Cloud Dependency**: TINA does not require an internet connection.
- **Local Storage**: All vector data and chat history are stored in `data/` and `vector_db/` on your machine.
- **Encrypted Thinking**: Your intellectual property never leaves your local environment.

---

## 📜 Getting Started

1.  **Dependencies**: Ensure `Ollama` is installed and running locally.
2.  **Launch**: Run `tina.bat` or `python main.py`.
3.  **Index**: Use the command palette (`Ctrl+Shift+P`) or `tina-index` to train the local brain on your codebase.

---

## 🔝 Recent Improvements

- **🧩 Plugin Manager UI**: A new dedicated interface for searching, enabling, and disabling project extensions on the fly (`src/ui/plugin_view.py`).
- **☁️ GitHub Integration**: Seamlessly synchronize your local development projects with GitHub for version control and remote collaboration.
- **🛠️ UI Refinements**: Continuous updates to the sidebar components, including enhanced AI and Git panel responsiveness.

---

*“Code at the speed of thought, with the security of a vault.”*
