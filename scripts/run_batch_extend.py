#!/usr/bin/env python3
"""
run_batch_extend.py — Wrapper to run batch_extend.py in background with logging.
"""
import subprocess, sys, os

collection = sys.argv[1] if len(sys.argv) > 1 else "unterkuenfte"
logfile = os.path.join(os.path.dirname(__file__), f"batch_{collection}.log")
script = os.path.join(os.path.dirname(__file__), "batch_extend.py")

print(f"Starting batch for {collection}, logging to {logfile}")

with open(logfile, "w", encoding="utf-8") as f:
    f.write(f"=== Batch started: {collection} ===\n")
    f.flush()

proc = subprocess.Popen(
    [sys.executable, "-u", script, collection, "--all"],
    cwd=os.path.dirname(os.path.dirname(script)),
    stdout=open(logfile, "a", encoding="utf-8"),
    stderr=subprocess.STDOUT,
)

print(f"PID: {proc.pid}")

# Write PID to a file for tracking
with open(logfile.replace(".log", ".pid"), "w") as f:
    f.write(str(proc.pid))

# Wait briefly then show first output
import time
time.sleep(5)
with open(logfile, encoding="utf-8") as f:
    content = f.read()
print(f"Initial output:\n{content}")
