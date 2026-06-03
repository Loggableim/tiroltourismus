"""
Submit a single image generation via curl (to bypass python subprocess issues)
and save it to the project.
Usage: python submit_and_wait.py <prompt> <prefix>
"""
import json, time, urllib.request, os, sys

COMFY = "http://127.0.0.1:8188"

def gen_and_save(prompt, negative, width, height, prefix, model="sd_xl_base_1.0.safetensors"):
    seed = int(time.time() * 1000) % 2**32
    
    wf = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 25, "cfg": 7.0,
            "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0]
        }},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}}
    }
    
    data = json.dumps({"prompt": wf, "client_id": f"gen_{prefix}"}).encode()
    req = urllib.request.Request(f"{COMFY}/prompt", data=data,
        headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid = resp["prompt_id"]
    print(f"Submitted {prefix} (pid={pid}) seed={seed}")
    sys.stdout.flush()
    
    # Poll
    for i in range(120):
        time.sleep(3)
        try:
            req = urllib.request.Request(f"{COMFY}/history/{pid}")
            hist = json.loads(urllib.request.urlopen(req, timeout=5).read())
        except Exception as e:
            print(f"  Poll error: {e}")
            continue
        if pid in hist:
            s = hist[pid].get("status", {})
            if s.get("completed"):
                outputs = hist[pid].get("outputs", {})
                for nid, o in outputs.items():
                    for img in o.get("images", []):
                        fn = img["filename"]
                        src = os.path.join(r"E:\HermesPortable\ComfyUI\output", fn)
                        if os.path.exists(src):
                            print(f"  DONE: {fn} ({os.path.getsize(src)//1024} KB)")
                            return src
                return None
            elif s.get("status_str") == "error":
                print(f"  ERROR")
                return None
    print(f"  TIMEOUT after 360s")
    return None

if __name__ == "__main__":
    PROMPT = sys.argv[1] if len(sys.argv) > 1 else "test"
    PREFIX = sys.argv[2] if len(sys.argv) > 2 else "test"
    W = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    H = int(sys.argv[4]) if len(sys.argv) > 4 else 768
    
    NEG = "photorealistic, 3d render, photograph, realistic texture, hyperrealistic, cinematic lighting, shadows, gradient, oil painting, airbrush, digital art, smooth shading"
    
    src = gen_and_save(PROMPT, NEG, W, H, PREFIX)
    if src:
        print(f"FILE:{src}")
