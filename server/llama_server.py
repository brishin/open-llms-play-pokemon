import modal

vllm_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm==0.7.2",
        "huggingface_hub[hf_transfer]==0.26.2",
        "flashinfer-python==0.2.0.post2",  # pinning, very unstable
        extra_index_url="https://flashinfer.ai/whl/cu124/torch2.5",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})  # faster model transfers
    .env({"VLLM_USE_V1": "1"})
)

MODELS_DIR = "/llamas"
MODEL_NAME = "neuralmagic/Meta-Llama-3.1-8B-Instruct-quantized.w4a16"
MODEL_REVISION = "a7c09948d9a632c2c840722f519672cd94af885d"

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

app = modal.App("example-vllm-openai-compatible")

API_KEY = "super-secret-key"  # api key, for auth. for production use, replace with a modal.Secret
MINUTES = 60
VLLM_PORT = 8000


@app.function(
    image=vllm_image,
    gpu="A10G",
    scaledown_window=2 * MINUTES,  # how long should we stay up with no requests?
    timeout=10 * MINUTES,  # how long should we wait for container start?
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=100)
@modal.web_server(port=VLLM_PORT, startup_timeout=5 * MINUTES)
def serve():
    import subprocess

    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        MODEL_NAME,
        "--revision",
        MODEL_REVISION,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--api-key",
        API_KEY,
        "--max-model-len",
        "8192",  # Reduce from default 131072 to 8192 tokens
        "--gpu-memory-utilization",
        "0.95",  # Use 95% of GPU memory instead of default 90%
    ]

    subprocess.Popen(" ".join(cmd), shell=True)


@app.local_entrypoint()
def test(test_timeout=10 * MINUTES):
    import json
    import time
    import urllib

    print(f"Running health check for server at {serve.get_web_url()}")
    up, start, delay = False, time.time(), 10
    while not up:
        try:
            with urllib.request.urlopen(serve.get_web_url() + "/health") as response:
                if response.getcode() == 200:
                    up = True
        except Exception:
            if time.time() - start > test_timeout:
                break
            time.sleep(delay)

    assert up, f"Failed health check for server at {serve.get_web_url()}"

    print(f"Successful health check for server at {serve.get_web_url()}")

    messages = [{"role": "user", "content": "Testing! Is this thing on?"}]
    print(f"Sending a sample message to {serve.get_web_url()}", *messages, sep="\n")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"messages": messages, "model": MODEL_NAME})
    req = urllib.request.Request(
        serve.get_web_url() + "/v1/chat/completions",
        data=payload.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        print(json.loads(response.read().decode()))
