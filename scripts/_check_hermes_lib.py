"""Test using the Hermes API client to make a request."""
import sys
sys.path.insert(0, r"C:\Users\logga\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages")

# Try importing the Hermes provider
try:
    from hermes_client import get_provider
    print("hermes_client available")
except ImportError:
    print("hermes_client not available")

# Try the llm module
try:
    from hermes.llm import get_chat_completion
    print("hermes.llm available")
except ImportError:
    print("hermes.llm not available")

# Try any hermes package
import pkg_resources
hermes_pkgs = [d for d in pkg_resources.working_set if 'hermes' in d.key.lower()]
print(f"Hermes packages: {[p.key for p in hermes_pkgs]}")
