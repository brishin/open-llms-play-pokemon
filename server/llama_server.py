from typing import Optional
import modal
import subprocess


MINUTES = 60

cuda_version = "12.4.0"  # should be no greater than host CUDA version
flavor = "devel"  #  includes full CUDA toolkit
operating_sys = "ubuntu22.04"
tag = f"{cuda_version}-{flavor}-{operating_sys}"

app = modal.App("llama-cpp-inference")

model_cache = modal.Volume.from_name("llamacpp-cache", create_if_missing=True)
cache_dir = "/root/.cache/llama.cpp"

download_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("huggingface_hub[hf_transfer]==0.26.2")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


@app.function(
    image=download_image, volumes={cache_dir: model_cache}, timeout=30 * MINUTES
)
def download_model(repo_id, allow_patterns, revision: Optional[str] = None):
    from huggingface_hub import snapshot_download

    print(f"🦙 downloading model from {repo_id} if not present")

    snapshot_download(
        repo_id=repo_id,
        revision=revision,
        local_dir=cache_dir,
        allow_patterns=allow_patterns,
    )

    model_cache.commit()  # ensure other Modal Functions can see our writes before we quit

    print("🦙 {repo_id} model loaded")


GPU_CONFIG = "L4"

inference_image = (
    modal.Image.from_registry(f"nvidia/cuda:{tag}", add_python="3.12")
    .apt_install("git", "build-essential", "cmake", "curl", "libcurl4-openssl-dev")
    .run_commands("git clone https://github.com/ggerganov/llama.cpp")
    .run_commands(
        "cmake llama.cpp -B llama.cpp/build "
        "-DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON -DLLAMA_CURL=ON "
    )
    .run_commands(  # this one takes a few minutes!
        "cmake --build llama.cpp/build --config Release -j --clean-first --target llama-server llama-cli"
    )
    .run_commands("cp llama.cpp/build/bin/llama-* llama.cpp")
    .entrypoint([])  # remove NVIDIA base container entrypoint
)


@app.function(
    image=inference_image,
    volumes={cache_dir: model_cache},
    gpu=GPU_CONFIG,
    timeout=3 * MINUTES,
)
@modal.concurrent(max_inputs=100)
@modal.web_server(8000)
def llama_cpp_server():
    model_entrypoint_file = "ARPO_UITARS1.5_7B.Q8_0.gguf"
    mmproj_file = "ARPO_UITARS1.5_7B.mmproj-Q8_0.gguf"

    # set layers to "off-load to", aka run on, GPU
    if GPU_CONFIG is not None:
        n_gpu_layers = 9999  # all
    else:
        n_gpu_layers = 0

    command = [
        "/llama.cpp/llama-server",
        "--model",
        f"{cache_dir}/{model_entrypoint_file}",
        "--n-gpu-layers",
        str(n_gpu_layers),
        "--mmproj",
        f"{cache_dir}/{mmproj_file}",
        "--ctx-size",
        "32768",
        "--jinja",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    print("🦙 running commmand:", command, sep="\n\t")
    subprocess.Popen(" ".join(command), shell=True)

    print("🦙 Server started successfully")
