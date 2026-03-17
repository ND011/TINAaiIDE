def setup():
    """Called when the plugin is loaded."""
    print("Hello World Plugin: Initialized!")

def on_file_open(file_path):
    """Triggered when a file is opened in the IDE."""
    print(f"Hello World Plugin: User opened {file_path}")
