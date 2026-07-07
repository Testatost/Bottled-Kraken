from __future__ import annotations
APP_NAME = "Bottled Kraken"
APP_VERSION = "3.3"
APP_DIR_NAME = "BottledKraken"
KRAKEN_VERSION = "7.0.2"
KRAKEN_REQUIREMENT = f"kraken=={KRAKEN_VERSION}"
PYTHON_BIDI_REQUIREMENT = "python-bidi>=0.6.7,<0.7"
DEFAULT_NVIDIA_CUDA_INDEX = "cu130"
DEFAULT_AMD_ROCM_INDEX = "rocm6.4"
# Static values are only fallbacks. The integrated installer resolves the newest
# available PyTorch CUDA/ROCm wheel index online at install time.
SUPPORTED_CUDA_INDEXES = ()
NVIDIA_TORCH_VERSION = ""
NVIDIA_TORCHVISION_VERSION = ""
BACKEND_DEFS = {
    "nvidia-cuda": {
        "name": "Bottled Kraken NVIDIA CUDA Backend",
        "short_name": "NVIDIA CUDA",
        "dir": "nvidia-cuda",
        "torch_index": DEFAULT_NVIDIA_CUDA_INDEX,
        "torch": NVIDIA_TORCH_VERSION,
        "torchvision": NVIDIA_TORCHVISION_VERSION,
    },
    "amd-rocm": {
        "name": "Bottled Kraken AMD ROCm Backend",
        "short_name": "AMD ROCm",
        "dir": "amd-rocm",
        "torch_index": DEFAULT_AMD_ROCM_INDEX,
        "torch": "",
        "torchvision": "",
    },
}
__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_DIR_NAME",
    "KRAKEN_VERSION",
    "KRAKEN_REQUIREMENT",
    "PYTHON_BIDI_REQUIREMENT",
    "DEFAULT_NVIDIA_CUDA_INDEX",
    "DEFAULT_AMD_ROCM_INDEX",
    "SUPPORTED_CUDA_INDEXES",
    "NVIDIA_TORCH_VERSION",
    "NVIDIA_TORCHVISION_VERSION",
    "BACKEND_DEFS",
]
