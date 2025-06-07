import modal

cuda_version = "12.8.0"  # should be no greater than host CUDA version
flavor = "devel"  #  includes full CUDA toolkit
operating_sys = "ubuntu22.04"
tag = f"{cuda_version}-{flavor}-{operating_sys}"

vllm_image = (
    modal.Image.from_registry(f"nvidia/cuda:{tag}", add_python="3.12")
    .pip_install(
        "vllm==0.9.0",
        "huggingface_hub[hf_transfer]==0.32.2",
        "flashinfer-python==0.2.5",
        extra_index_url="https://flashinfer.ai/whl/cu124/torch2.6",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})  # faster model transfers
    .env({"VLLM_USE_V1": "1"})
)

MODEL_NAME = "ByteDance-Seed/UI-TARS-1.5-7B"
MODEL_REVISION = "683d002dd99d8f95104d31e70391a39348857f4e"

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

app = modal.App("pokemon-llm-server")

API_KEY = "super-secret-key"  # api key, for auth. for production use, replace with a modal.Secret
MINUTES = 60
VLLM_PORT = 8000


@app.function(
    image=vllm_image,
    gpu="A10G",
    scaledown_window=2 * MINUTES,  # how long should we stay up with no requests?
    timeout=20 * MINUTES,  # how long should we wait for container start?
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
        "--trust-remote-code",
        "--dtype",
        "bfloat16",
        "--max-model-len",
        "16384",
        "--limit-mm-per-prompt",
        "image=5,video=5",
        "--gpu-memory-utilization",
        "0.95",
    ]

    subprocess.Popen(" ".join(cmd), shell=True)


@app.local_entrypoint()
def test(test_timeout=20 * MINUTES):
    import json
    import time
    import urllib.request

    base_url = serve.get_web_url()
    if base_url is None:
        raise RuntimeError("Server URL is not available")

    print(f"Running health check for server at {base_url}")
    up, start, delay = False, time.time(), 10
    while not up:
        try:
            with urllib.request.urlopen(base_url + "/health") as response:
                if response.getcode() == 200:
                    up = True
        except Exception:
            if time.time() - start > test_timeout:
                break
            time.sleep(delay)

    assert up, f"Failed health check for server at {base_url}"

    print(f"Successful health check for server at {base_url}")

    messages = [{"role": "user", "content": "Testing! Is this thing on?"}]
    print(f"Sending a sample message to {base_url}", *messages, sep="\n")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"messages": messages, "model": MODEL_NAME})
    req = urllib.request.Request(
        base_url + "/v1/chat/completions",
        data=payload.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        print(json.loads(response.read().decode()))
