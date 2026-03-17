import os
import json

class ProjectTemplateManager:
    """Manages project templates and scaffolding for new projects."""
    
    TEMPLATES = {
        "Python": {
            "description": "Basic Python project with main.py and requirements.txt",
            "files": {
                "main.py": 'def main():\n    print("Hello from Tina AI Project!")\n\nif __name__ == "__main__":\n    main()\n',
                "requirements.txt": "customtkinter\npillow\n",
                "README.md": "# Python Project\n\nCreated with Tina AI COD.\n"
            }
        },
        "Web": {
            "description": "Simple Web project with HTML, CSS, and JS",
            "files": {
                "index.html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>New Web Project</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <h1>Hello from Tina AI!</h1>\n    <script src="script.js"></script>\n</body>\n</html>',
                "style.css": 'body {\n    background-color: #1a1a1a;\n    color: white;\n    font-family: sans-serif;\n    display: flex;\n    justify-content: center;\n    align-items: center;\n    height: 100vh;\n    margin: 0;\n}',
                "script.js": 'console.log("Web project initialized by Tina AI.");\n'
            }
        },
        "Node.js": {
            "description": "Basic Node.js project with package.json",
            "files": {
                "index.js": 'console.log("Node.js project running...");\n',
                "package.json": '{\n  "name": "new-node-project",\n  "version": "1.0.0",\n  "main": "index.js",\n  "scripts": {\n    "start": "node index.js"\n  }\n}'
            }
        }
    }

    @staticmethod
    def create_project(project_type, base_path, project_name):
        """Creates a new project from a template."""
        if project_type not in ProjectTemplateManager.TEMPLATES:
            return False, f"Unknown project type: {project_type}"
        
        target_dir = os.path.join(base_path, project_name)
        
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            template = ProjectTemplateManager.TEMPLATES[project_type]
            for filename, content in template["files"].items():
                file_path = os.path.join(target_dir, filename)
                # If it's package.json, customize the name
                if filename == "package.json":
                    try:
                        data = json.loads(content)
                        data["name"] = project_name.lower().replace(" ", "-")
                        content = json.dumps(data, indent=2)
                    except: pass

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            return True, target_dir
        except Exception as e:
            return False, str(e)
