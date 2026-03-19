import importlib.util
import os
import json

class PluginManager:
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.plugins = {} # name -> module
        self.enabled_plugins = {} # name -> bool
        self.config_path = os.path.join(os.path.dirname(plugin_dir), "data", "plugins_config.json")
        self.load_config()

    def load_config(self):
        """Loads enabled/disabled state from config file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    self.enabled_plugins = json.load(f)
            except:
                self.enabled_plugins = {}

    def save_config(self):
        """Saves current states to config file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.enabled_plugins, f, indent=4)

    def discover_plugins(self):
        """Looks for .py files in the plugin directory."""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_name = filename[:-3]
                if plugin_name not in self.enabled_plugins:
                    self.enabled_plugins[plugin_name] = True # Default to enabled
                
                if self.enabled_plugins[plugin_name]:
                    self.load_plugin(plugin_name)
        self.save_config()

    def load_plugin(self, name):
        """Dynamically imports a plugin module."""
        file_path = os.path.join(self.plugin_dir, f"{name}.py")
        if not os.path.exists(file_path): return
        
        spec = importlib.util.spec_from_file_location(name, file_path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, "setup"):
                self.plugins[name] = module
                print(f"Plugin loaded: {name}")
        except Exception as e:
            print(f"Failed to load plugin {name}: {e}")

    def toggle_plugin(self, name, state):
        """Enable or disable a plugin."""
        self.enabled_plugins[name] = state
        self.save_config()
        if state:
            self.load_plugin(name)
        else:
            if name in self.plugins:
                del self.plugins[name]
                print(f"Plugin disabled: {name}")

    def execute_plugin_hook(self, hook_name, *args, **kwargs):
        """Executes a specific function in all enabled plugins."""
        for name, module in self.plugins.items():
            if hasattr(module, hook_name):
                try:
                    getattr(module, hook_name)(*args, **kwargs)
                except Exception as e:
                    print(f"Error executing hook {hook_name} in {name}: {e}")
                    
    def get_all_plugin_info(self):
        """Returns a list of all plugins and their status."""
        all_info = []
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                name = filename[:-3]
                all_info.append({
                    "name": name,
                    "enabled": self.enabled_plugins.get(name, False),
                    "loaded": name in self.plugins
                })
        return all_info
