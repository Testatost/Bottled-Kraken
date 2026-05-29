import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
warnings.filterwarnings("ignore", message=r"invalid escape sequence.*\\_", category=SyntaxWarning)
try:
    from bottled_kraken.tools.release_zip_autogen import ensure_release_zip_for_tests
    ensure_release_zip_for_tests()
except Exception:
    pass
def main():
    from bottled_kraken.app import main as run_app
    return run_app()
__all__ = ["main"]
