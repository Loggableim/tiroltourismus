"""Find hermes package specifically."""
import subprocess, sys

result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=columns"], 
                       capture_output=True, text=True)
for line in result.stdout.splitlines():
    if 'hermes' in line.lower() or 'opencode' in line.lower():
        print(line)
