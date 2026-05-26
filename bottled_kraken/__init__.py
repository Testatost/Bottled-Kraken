import warnings

# Keep third-party import warnings from coremltools out of the GUI/IDE console.
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
warnings.filterwarnings("ignore", message=r"invalid escape sequence.*\\_", category=SyntaxWarning)

try:
    from .tools.release_zip_autogen import ensure_release_zip_for_tests
    ensure_release_zip_for_tests()
except Exception:
    pass

from .app import main
