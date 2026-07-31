import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
warnings.filterwarnings("ignore", message=r"invalid escape sequence.*\\_", category=SyntaxWarning)


def main():
    """Start the Bottled Kraken desktop application."""
    from bottled_kraken.kraken_update import activate_kraken_overlay

    activate_kraken_overlay()
    from bottled_kraken.app import main as run_app
    return run_app()


__all__ = ["main"]
