"""Find Hermes packages."""
import subprocess, sys

# Check what's installed
result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=columns"], 
                       capture_output=True, text=True)
print(result.stdout[:2000])
