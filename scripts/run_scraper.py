"""Run scraper with verbose output."""
import subprocess, sys
p = subprocess.Popen(
    [sys.executable, "scripts/osm_gastro_scraper.py"],
    cwd="F:/tiroltourismus",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env={"DRY_RUN": "1", "OSM_TIMEOUT": "180", "PYTHONUNBUFFERED": "1"},
)
import time
t0 = time.time()
while True:
    if p.poll() is not None:
        break
    elapsed = time.time() - t0
    if elapsed > 60:
        print("60s elapsed, terminating...", flush=True)
        p.kill()
        break
    time.sleep(1)

out, err = p.communicate(timeout=5)
if out:
    print("STDOUT:", out.decode()[:2000])
if err:
    print("STDERR:", err.decode()[:2000])
print(f"\nExit code: {p.returncode}")
