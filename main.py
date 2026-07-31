import sys
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
warnings.filterwarnings("ignore", message=r"invalid escape sequence.*\\_", category=SyntaxWarning)


def _run_internal_cli() -> int | None:
    if len(sys.argv) < 2:
        return None
    command = sys.argv[1]
    if command == "--bk-whisper-transcribe":
        from bottled_kraken.whisper_runtime import run_whisper_transcription_cli

        return run_whisper_transcription_cli(sys.argv[2:])
    if command == "--bk-validate-kraken-overlay":
        if len(sys.argv) != 3:
            return 2
        from bottled_kraken.kraken_update import validate_kraken_overlay_cli

        return validate_kraken_overlay_cli(sys.argv[2])
    return None


if __name__ == "__main__":
    exit_code = _run_internal_cli()
    if exit_code is not None:
        raise SystemExit(exit_code)
    from bottled_kraken import main

    main()
