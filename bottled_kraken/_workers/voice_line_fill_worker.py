"""Worker-Klassen für Bottled Kraken."""
from ..shared import *

class VoiceLineFillWorker(QThread):
    finished_line = Signal(str, int, str)  # path, line_index, text
    failed_line = Signal(str, str)  # path, error_message
    progress_changed = Signal(int)  # 0..100
    status_changed = Signal(str)  # status text
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
            parent=None
    ):
        super().__init__(parent)
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
    def _tr(self, *args):
        if len(args) == 1:
            return QCoreApplication.translate("VoiceLineFillWorker", args[0])
        return QCoreApplication.translate(*args)
    def stop(self):
        # normales Ende der Aufnahme -> Worker beendet den Stream selbst
        self._finish_requested = True
    def cancel(self):
        # echter Abbruch -> Worker beendet den Stream selbst
        self._cancel_requested = True
        self.requestInterruption()
        self._finish_requested = False
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            # optional für Debug
            try:
                self.status_changed.emit(f"Audio-Status: {status}")
            except Exception:
                pass
        if indata is not None and len(indata):
            self._audio_chunks.append(indata.copy())
        if self._cancel_requested or self._finish_requested:
            raise sd.CallbackStop()
    def _record_until_stop(self):
        self.status_changed.emit(
            f"Aufnahmegerät: {self.input_device} | Samplerate: {self.input_samplerate or 'auto'}"
        )
        self.status_changed.emit("Mikrofon aktiv. Bitte nur die aktuell ausgewählte Zeile diktieren.")
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
                callback=self._audio_callback
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
        if sys.platform.startswith("win"):
            base = r"C:\bk_temp"
        else:
            base = "/tmp/bk_temp"
        os.makedirs(base, exist_ok=True)
        return base
    def _write_temp_wav(self) -> str:
        if not self._audio_chunks:
            raise RuntimeError(self._tr("warn_voice_no_audio_data"))
        audio = np.concatenate(self._audio_chunks, axis=0).flatten()
        min_samples = int(0.35 * max(1, getattr(self, "_record_samplerate", VOICE_SAMPLE_RATE)))
        if len(audio) < min_samples:
            raise RuntimeError("Aufnahme zu kurz. Bitte etwas länger sprechen.")
        audio = np.clip(audio, -1.0, 1.0)
        tmp_dir = os.path.join(self._safe_ascii_temp_root(), "voice")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(
            tmp_dir,
            f"voice_{int(time.time() * 1000)}.wav"
        )
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
        # wichtig: längere Begriffe zuerst
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
        # Punkt vor Doppelpunkt automatisch entfernen:
        # "Ort.:" / "Ort. :" / "Ort :" -> "Ort:"
        txt = re.sub(r"\.\s*:", ":", txt)
        # kein Leerzeichen vor klassischen Satzzeichen
        txt = re.sub(r"\s+([.,:;?!%€)\]])", r"\1", txt)
        # kein Leerzeichen nach öffnenden Klammern
        txt = re.sub(r"([(\[\{])\s+", r"\1", txt)
        # keine Leerzeichen um technische Zeichen
        txt = re.sub(r"\s*([/\-=+*_#])\s*", r"\1", txt)
        # Doppelte Spaces glätten
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt
    def _postprocess_transcript(self, text: str) -> str:
        txt = (text or "").strip()
        # gesprochene Satzzeichen zuerst in Platzhalter umwandeln
        txt = self._replace_spoken_punctuation_with_placeholders(txt)
        # automatische Satzendzeichen von Whisper nur entfernen,
        # wenn sie NICHT aus einem Platzhalter entstanden sind
        txt = re.sub(r"[.!?]+$", "", txt).strip()
        # Platzhalter zurückwandeln
        txt = self._restore_punctuation_placeholders(txt)
        return re.sub(r"\s+", " ", txt).strip()
    def run(self):
        tmp_wav = None
        try:
            self._audio_chunks = []
            if not os.path.isdir(self.model_dir):
                raise RuntimeError("Faster-Whisper-Modellordner wurde nicht gefunden.")
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
            from faster_whisper import WhisperModel
            safe_model_dir = os.path.abspath(self.model_dir)
            safe_wav_path = os.path.abspath(tmp_wav)
            kwargs = {
                "beam_size": 5,
                "vad_filter": False,
                "condition_on_previous_text": False,
                "task": "transcribe",
                "language": None,
            }
            active_device = self.device
            active_compute = self.compute_type
            try:
                model = WhisperModel(
                    safe_model_dir,
                    device=active_device,
                    compute_type=active_compute
                )
                self.status_changed.emit(
                    self._tr("voice_status_transcribe_line", active_device, active_compute)
                )
                self.progress_changed.emit(60)
                segments, info = model.transcribe(safe_wav_path, **kwargs)
            except Exception as e:
                msg = str(e).lower()
                if active_device == "cuda" and ("out of memory" in msg or "cuda failed" in msg):
                    try:
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except Exception:
                        pass
                    self.status_changed.emit(
                        "CUDA-Speicher voll – Whisper wechselt automatisch auf CPU..."
                    )
                    model = WhisperModel(
                        safe_model_dir,
                        device="cpu",
                        compute_type="int8"
                    )
                    self.status_changed.emit("Transkribiere ausgewählte Zeile lokal (cpu/int8)...")
                    self.progress_changed.emit(60)
                    segments, info = model.transcribe(safe_wav_path, **kwargs)
                else:
                    raise
            try:
                detected_lang = getattr(info, "language", None)
                if detected_lang:
                    self.status_changed.emit(f"Erkannte Sprache: {detected_lang}")
            except Exception:
                pass
            segments = list(segments)
            full_text = " ".join((seg.text or "").strip() for seg in segments).strip()
            full_text = self._postprocess_transcript(full_text)
            if not full_text:
                raise RuntimeError("Es konnte kein verständlicher Text erkannt werden.")
            self.progress_changed.emit(100)
            self.finished_line.emit(self.path, self.line_index, full_text)
        except Exception as e:
            self.failed_line.emit(self.path, str(e))
        finally:
            if tmp_wav and os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass
