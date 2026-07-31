from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from bottled_kraken.common import (
    Optional,
    QThread,
    Signal,
    VOICE_BLOCKSIZE,
    VOICE_CHANNELS,
    VOICE_SAMPLE_RATE,
    np,
    re,
    sd,
    translation,
    wave,
)
from bottled_kraken.runtime_cli import hidden_process_kwargs
from bottled_kraken.runtime_logging import get_logger
from bottled_kraken.whisper_runtime import (
    parse_whisper_subprocess_output,
    utf8_child_environment,
    whisper_transcription_command,
)


_LOGGER = get_logger("voice")


class VoiceLineFillWorker(QThread):
    finished_line = Signal(str, int, str)
    failed_line = Signal(str, str)
    progress_changed = Signal(int)
    status_changed = Signal(str)

    def __init__(
        self,
        path: str,
        line_index: int,
        model_dir: str,
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None,
        input_device=None,
        input_samplerate: Optional[int] = None,
        tr_func=None,
        parent=None,
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr(translation.DEFAULT_LANGUAGE)
        self.path = path
        self.line_index = int(line_index)
        self.model_dir = model_dir
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.input_device = input_device
        self.input_samplerate = int(input_samplerate) if input_samplerate else None
        self._finish_requested = False
        self._cancel_requested = False
        self._audio_chunks = []
        self._stream = None
        self._transcribe_process: subprocess.Popen | None = None

    def stop(self):
        self._finish_requested = True

    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()
        self._finish_requested = False
        self._terminate_transcription_process()

    def _terminate_transcription_process(self) -> None:
        process = self._transcribe_process
        if process is None or process.poll() is not None:
            return
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except Exception:
            try:
                process.terminate()
            except Exception:
                return
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "nt":
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            try:
                self.status_changed.emit(self._tr("voice_status_audio_status", status))
            except Exception:
                pass
        if indata is not None and len(indata):
            self._audio_chunks.append(indata.copy())
        if self._cancel_requested or self._finish_requested:
            raise sd.CallbackStop()

    def _record_until_stop(self):
        self.status_changed.emit(
            self._tr(
                "voice_status_input_device_detail",
                self.input_device,
                self.input_samplerate or self._tr("voice_status_input_samplerate_auto"),
            )
        )
        self.status_changed.emit(self._tr("voice_status_microphone_active"))
        self.progress_changed.emit(5)
        samplerate = self.input_samplerate
        if not samplerate:
            try:
                dev_info = sd.query_devices(self.input_device, "input")
                samplerate = int(dev_info.get("default_samplerate", VOICE_SAMPLE_RATE))
            except Exception:
                samplerate = VOICE_SAMPLE_RATE
        try:
            sd.check_input_settings(
                device=self.input_device,
                samplerate=samplerate,
                channels=VOICE_CHANNELS,
                dtype="float32",
            )
        except Exception:
            samplerate = VOICE_SAMPLE_RATE
        self._record_samplerate = int(samplerate)
        self._stream = None
        stream = None
        try:
            stream = sd.InputStream(
                device=self.input_device,
                samplerate=self._record_samplerate,
                channels=VOICE_CHANNELS,
                dtype="float32",
                blocksize=VOICE_BLOCKSIZE,
                callback=self._audio_callback,
            )
            self._stream = stream
            stream.start()
            while stream.active:
                if self._cancel_requested or self.isInterruptionRequested():
                    try:
                        stream.abort(ignore_errors=True)
                    except Exception:
                        pass
                    break
                if self._finish_requested:
                    try:
                        stream.abort(ignore_errors=True)
                    except Exception:
                        pass
                    break
                self.msleep(20)
        finally:
            try:
                if stream is not None:
                    try:
                        stream.stop()
                    except Exception:
                        pass
                    try:
                        stream.close()
                    except Exception:
                        pass
            finally:
                self._stream = None

    def _safe_ascii_temp_root(self) -> str:
        if os.name != "nt":
            try:
                uid = os.getuid()
            except AttributeError:
                uid = 0
            base = Path("/tmp") / f"bk-voice-{uid}"
        else:
            base = Path(tempfile.gettempdir()) / "bk-voice"
        base.mkdir(parents=True, exist_ok=True)
        try:
            base.chmod(0o700)
        except OSError:
            pass
        return str(base)

    def _safe_model_alias(self) -> str:
        source = Path(self.model_dir).expanduser().resolve()
        if os.name == "nt":
            return str(source)
        try:
            uid = os.getuid()
        except AttributeError:
            uid = 0
        digest = hashlib.sha256(os.fsencode(str(source))).hexdigest()[:16]
        alias_root = Path("/tmp") / f"bk-whisper-{uid}" / "models"
        alias_root.mkdir(parents=True, exist_ok=True)
        try:
            alias_root.parent.chmod(0o700)
            alias_root.chmod(0o700)
        except OSError:
            pass
        alias = alias_root / digest
        try:
            if alias.is_symlink() and alias.resolve() == source:
                return str(alias)
            if alias.exists() or alias.is_symlink():
                alias.unlink()
            alias.symlink_to(source, target_is_directory=True)
            return str(alias)
        except OSError:
            return str(source)

    def _write_temp_wav(self) -> str:
        if not self._audio_chunks:
            raise RuntimeError(self._tr("warn_voice_no_audio_data"))
        audio = np.concatenate(self._audio_chunks, axis=0).flatten()
        min_samples = int(0.35 * max(1, getattr(self, "_record_samplerate", VOICE_SAMPLE_RATE)))
        if len(audio) < min_samples:
            raise RuntimeError(self._tr("voice_error_recording_too_short"))
        audio = np.clip(audio, -1.0, 1.0)
        tmp_dir = self._safe_ascii_temp_root()
        tmp_path = os.path.join(tmp_dir, f"voice_{int(time.time() * 1000)}.wav")
        pcm16 = (audio * 32767.0).astype(np.int16)
        samplerate = int(getattr(self, "_record_samplerate", VOICE_SAMPLE_RATE))
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(VOICE_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(pcm16.tobytes())
        return tmp_path

    def _replace_spoken_punctuation_with_placeholders(self, text: str) -> str:
        txt = (text or "").strip()
        replacements = [
            (r"\bschräg\s*strich\b[.,;:!?]?", " <<SLASH>> "),
            (r"\bslash\b[.,;:!?]?", " <<SLASH>> "),
            (r"\bdoppel\s*punkt\b[.,;:!?]?", " <<COLON>> "),
            (r"\bsemi\s*kolon\b[.,;:!?]?", " <<SEMICOLON>> "),
            (r"\bfrage\s*zeichen\b[.,;:!?]?", " <<QUESTION>> "),
            (r"\bausrufe\s*zeichen\b[.,;:!?]?", " <<EXCLAMATION>> "),
            (r"\banführungs\s*zeichen\b[.,;:!?]?", " <<QUOTE>> "),
            (r"\bgänse\s*füßchen\b[.,;:!?]?", " <<QUOTE>> "),
            (r"\bgleichheits\s*zeichen\b[.,;:!?]?", " <<EQUALS>> "),
            (r"\bklammer\s+auf\b[.,;:!?]?", " <<LPAREN>> "),
            (r"\bklammer\s+zu\b[.,;:!?]?", " <<RPAREN>> "),
            (r"\bbinde\s*strich\b[.,;:!?]?", " <<HYPHEN>> "),
            (r"\bunter\s*strich\b[.,;:!?]?", " <<UNDERSCORE>> "),
            (r"\bkomma\b[.,;:!?]?", " <<COMMA>> "),
            (r"\bpunkt\b[.,;:!?]?", " <<DOT>> "),
            (r"\bminus\b[.,;:!?]?", " <<HYPHEN>> "),
            (r"\bgleich\b[.,;:!?]?", " <<EQUALS>> "),
            (r"\bprozent\b[.,;:!?]?", " <<PERCENT>> "),
            (r"\beuro\b[.,;:!?]?", " <<EURO>> "),
            (r"\braute\b[.,;:!?]?", " <<HASH>> "),
            (r"\bhashtag\b[.,;:!?]?", " <<HASH>> "),
            (r"\bplus\b[.,;:!?]?", " <<PLUS>> "),
            (r"\bstern\b[.,;:!?]?", " <<ASTERISK>> "),
            (r"\basterisk\b[.,;:!?]?", " <<ASTERISK>> "),
            (r"\bunderscore\b[.,;:!?]?", " <<UNDERSCORE>> "),
        ]
        for pattern, repl in replacements:
            txt = re.sub(pattern, repl, txt, flags=re.IGNORECASE)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt
    def _restore_punctuation_placeholders(self, text: str) -> str:
        txt = f" {(text or '').strip()} "
        replacements = {
            "<<SLASH>>": "/",
            "<<DOT>>": ".",
            "<<COLON>>": ":",
            "<<HYPHEN>>": "-",
            "<<COMMA>>": ",",
            "<<SEMICOLON>>": ";",
            "<<QUESTION>>": "?",
            "<<EXCLAMATION>>": "!",
            "<<QUOTE>>": "\"",
            "<<EURO>>": "€",
            "<<EQUALS>>": "=",
            "<<PERCENT>>": "%",
            "<<LPAREN>>": "(",
            "<<RPAREN>>": ")",
            "<<HASH>>": "#",
            "<<PLUS>>": "+",
            "<<ASTERISK>>": "*",
            "<<UNDERSCORE>>": "_",
        }
        for placeholder, char in replacements.items():
            txt = txt.replace(placeholder, char)
        txt = re.sub(r"\.\s*:", ":", txt)
        txt = re.sub(r"\s+([.,:;?!%€)\]])", r"\1", txt)
        txt = re.sub(r"([(\[\{])\s+", r"\1", txt)
        txt = re.sub(r"\s*([/\-=+*_#])\s*", r"\1", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt
    def _postprocess_transcript(self, text: str) -> str:
        txt = (text or "").strip()
        txt = self._replace_spoken_punctuation_with_placeholders(txt)
        txt = re.sub(r"[.!?]+$", "", txt).strip()
        txt = self._restore_punctuation_placeholders(txt)
        return re.sub(r"\s+", " ", txt).strip()
    def _transcribe_in_utf8_subprocess(self, wav_path: str) -> dict:
        model_dir = self._safe_model_alias()
        command = whisper_transcription_command(
            model_dir=model_dir,
            wav_path=wav_path,
            device=self.device,
            compute_type=self.compute_type,
            language=self.language,
        )
        output_path = Path(self._safe_ascii_temp_root()) / f"whisper_{int(time.time() * 1000)}.log"
        kwargs = hidden_process_kwargs()
        if os.name != "nt":
            kwargs["start_new_session"] = True
        self.status_changed.emit(self._tr("voice_status_transcribe_line", self.device, self.compute_type))
        self.progress_changed.emit(60)
        returncode = -1
        try:
            with output_path.open("wb") as output:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    env=utf8_child_environment(),
                    **kwargs,
                )
                self._transcribe_process = process
                progress = 60
                while process.poll() is None:
                    if self._cancel_requested or self.isInterruptionRequested():
                        self._terminate_transcription_process()
                        raise RuntimeError(self._tr("warn_voice_cancelled"))
                    progress = min(92, progress + 1)
                    self.progress_changed.emit(progress)
                    self.msleep(250)
                returncode = int(process.wait())
            if self._cancel_requested or self.isInterruptionRequested():
                raise RuntimeError(self._tr("warn_voice_cancelled"))
            raw = output_path.read_bytes()
        finally:
            self._transcribe_process = None
            try:
                output_path.unlink()
            except OSError:
                pass
        payload = parse_whisper_subprocess_output(raw)
        if returncode != 0 or not payload.get("ok"):
            detail = str(payload.get("traceback") or payload.get("error") or "")
            if detail:
                _LOGGER.error("Whisper subprocess failed:\n%s", detail)
            message = str(payload.get("error") or self._tr("voice_error_transcription_failed"))
            raise RuntimeError(message)
        return payload

    def run(self):
        tmp_wav = None
        try:
            self._audio_chunks = []
            if not os.path.isdir(self.model_dir):
                raise RuntimeError(self._tr("voice_error_model_dir_missing"))
            self.progress_changed.emit(0)
            self._record_until_stop()
            if self._cancel_requested or self.isInterruptionRequested():
                raise RuntimeError(self._tr("warn_voice_cancelled"))
            if not self._finish_requested:
                raise RuntimeError(self._tr("warn_voice_not_finished"))
            if not self._audio_chunks:
                raise RuntimeError(self._tr("warn_voice_no_audio_data"))
            self.status_changed.emit(self._tr("voice_status_prepare_wav"))
            self.progress_changed.emit(20)
            tmp_wav = self._write_temp_wav()
            self.status_changed.emit(self._tr("voice_status_load_whisper"))
            self.progress_changed.emit(35)
            payload = self._transcribe_in_utf8_subprocess(tmp_wav)
            active_device = str(payload.get("device") or self.device)
            active_compute = str(payload.get("compute_type") or self.compute_type)
            if self.device == "cuda" and active_device == "cpu":
                self.status_changed.emit(self._tr("voice_status_cuda_fallback"))
                self.status_changed.emit(self._tr("voice_status_cpu_transcribe"))
            detected_lang = str(payload.get("language") or "")
            if detected_lang:
                self.status_changed.emit(self._tr("voice_status_detected_language", detected_lang))
            full_text = self._postprocess_transcript(str(payload.get("text") or ""))
            if not full_text:
                raise RuntimeError(self._tr("voice_error_no_understandable_text"))
            self.progress_changed.emit(100)
            self.finished_line.emit(self.path, self.line_index, full_text)
        except Exception as exc:
            _LOGGER.exception(
                "Whisper line dictation failed for %s line %s",
                self.path,
                self.line_index + 1,
            )
            self.failed_line.emit(self.path, str(exc))
        finally:
            self._transcribe_process = None
            if tmp_wav and os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass
