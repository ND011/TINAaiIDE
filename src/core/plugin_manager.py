import importlib.util
import os

class PluginManager:
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.plugins = {}

    def discover_plugins(self):
        """Looks for .py files in the plugin directory and loads them."""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_name = filename[:-3]
                self.load_plugin(plugin_name)

    def load_plugin(self, name):
        """Dynamically imports a plugin module."""
        file_path = os.path.join(self.plugin_dir, f"{name}.py")
        spec = importlib.util.spec_from_file_location(name, file_path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, "setup"):
                self.plugins[name] = module
                print(f"Plugin loaded: {name}")
        except Exception as e:
            print(f"Failed to load plugin {name}: {e}")

    def execute_plugin_hook(self, hook_name, *args, **kwargs):
        """Executes a specific function in all loaded plugins."""
        for name, module in self.plugins.items():
            if hasattr(module, hook_name):
                try:
                    getattr(module, hook_name)(*args, **kwargs)
                except Exception as e:
                    print(f"Error executing hook {hook_name} in {name}: {e}")
