from __future__ import annotations

"""Windows-only CoreML import shim for Kraken.

Kraken 7 imports ``coremltools.proto.NeuralNetwork_pb2`` while loading its VGSL
layers. Bottled Kraken does not use CoreML export or CoreML inference on
Windows, and coremltools is not a normal Windows runtime dependency for this
build. The shim only satisfies Kraken's import-time protobuf references; if a
real CoreML operation is reached it fails with an explicit RuntimeError.
"""

import importlib.util
import os
import sys
import types
from typing import Any


class _CoreMLUnavailable(RuntimeError):
    pass


class _CoreMLStubMessage:
    """Permissive placeholder for protobuf message classes used at import time."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._bk_coreml_args = args
        self._bk_coreml_kwargs = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> "_CoreMLStubMessage":
        return _CoreMLStubMessage(*args, **kwargs)

    def __getattr__(self, name: str) -> "_CoreMLStubMessage":
        value = _CoreMLStubMessage()
        setattr(self, name, value)
        return value

    def CopyFrom(self, _other: Any) -> None:
        return None

    def MergeFrom(self, _other: Any) -> None:
        return None

    def SerializeToString(self, *args: Any, **kwargs: Any) -> bytes:
        raise _CoreMLUnavailable(
            "CoreML export is not available in the Bottled Kraken Windows build."
        )


class _CoreMLStubClass(_CoreMLStubMessage):
    pass


def _make_message_class(name: str) -> type[_CoreMLStubMessage]:
    return type(str(name), (_CoreMLStubMessage,), {})


def _install_module(name: str, *, package: bool = False) -> types.ModuleType:
    module = sys.modules.get(name)
    if isinstance(module, types.ModuleType):
        return module
    module = types.ModuleType(name)
    module.__file__ = "<bottled-kraken-windows-coremltools-stub>"
    module.__package__ = name if package else name.rpartition(".")[0]
    if package:
        module.__path__ = []  # type: ignore[attr-defined]
    sys.modules[name] = module
    return module


def _attach_dynamic_protobuf(module: types.ModuleType) -> None:
    def __getattr__(name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        value = _make_message_class(name)
        setattr(module, name, value)
        return value

    module.__getattr__ = __getattr__  # type: ignore[attr-defined]
    module.DESCRIPTOR = _CoreMLStubMessage()


def _attach_dynamic_module(module: types.ModuleType) -> None:
    def __getattr__(name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        value = _CoreMLStubClass
        setattr(module, name, value)
        return value

    module.__getattr__ = __getattr__  # type: ignore[attr-defined]


def install_windows_coremltools_stub() -> bool:
    """Installs a minimal CoreML module tree on Windows when coremltools is absent."""

    if not sys.platform.startswith("win"):
        return False
    if os.environ.get("BOTTLED_KRAKEN_USE_REAL_COREMLTOOLS", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        return False
    try:
        if importlib.util.find_spec("coremltools") is not None:
            return False
    except Exception:
        pass

    coreml = _install_module("coremltools", package=True)
    proto = _install_module("coremltools.proto", package=True)
    nn = _install_module("coremltools.proto.NeuralNetwork_pb2")
    model_pb2 = _install_module("coremltools.proto.Model_pb2")
    feature_pb2 = _install_module("coremltools.proto.FeatureTypes_pb2")
    models = _install_module("coremltools.models", package=True)
    neural_network = _install_module("coremltools.models.neural_network", package=True)
    builder = _install_module("coremltools.models.neural_network.builder")
    datatypes = _install_module("coremltools.models.neural_network.datatypes")

    for module in (nn, model_pb2, feature_pb2):
        _attach_dynamic_protobuf(module)
    for module in (models, neural_network, builder, datatypes):
        _attach_dynamic_module(module)

    proto.NeuralNetwork_pb2 = nn  # type: ignore[attr-defined]
    proto.Model_pb2 = model_pb2  # type: ignore[attr-defined]
    proto.FeatureTypes_pb2 = feature_pb2  # type: ignore[attr-defined]
    neural_network.builder = builder  # type: ignore[attr-defined]
    neural_network.datatypes = datatypes  # type: ignore[attr-defined]
    models.neural_network = neural_network  # type: ignore[attr-defined]
    coreml.proto = proto  # type: ignore[attr-defined]
    coreml.models = models  # type: ignore[attr-defined]
    coreml.__version__ = "0+windows-stub"  # type: ignore[attr-defined]
    return True
