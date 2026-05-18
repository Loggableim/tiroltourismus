import subprocess, sys, os, time

collection = sys.argv[1] if len(sys.argv) > 1 else "unterkuenfte"
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
log_file = os.path.join(script_dir, f"batch_{collection}.log")
pid_file = os.path.join(script_dir, f"batch_{collection}.pid")

# Clear previous log
with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"=== Batch started: {collection} at {time.strftime('%H:%M:%S')} ===\n")

with open(log_file, "a", encoding="utf-8") as f:
    proc = subprocess.Popen(
        [sys.executable, "-u", os.path.join(script_dir, "batch_extend.py"), collection, "--all"],
        cwd=project_dir,
        stdout=f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
    )

with open(pid_file, "w") as f:
    f.write(str(proc.pid))

print(f"Started {collection} batch, PID={proc.pid}")
print(f"Log: {log_file}")
