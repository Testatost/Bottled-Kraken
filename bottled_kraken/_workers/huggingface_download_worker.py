"""Worker-Klassen für Bottled Kraken."""
from ..shared import *

class HFDownloadWorker(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_download = Signal(str)
    failed_download = Signal(str)
    def __init__(
            self,
            repo_id: str,
            local_dir: str,
            prepare_cmds: List[List[str]],
            install_cmd: List[str],
            download_cmd: List[str],
            tr_func=None,
            parent=None
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr("de")
        self.repo_id = repo_id
        self.local_dir = local_dir
        self.prepare_cmds = prepare_cmds or []
        self.install_cmd = install_cmd
        self.download_cmd = download_cmd
        self._proc = None
        self._cancel_requested = False
        self._last_status_line = ""
        self._current_file = ""
        self._last_finished_file = ""
        self._repo_files: List[Tuple[str, int]] = []  # [(rel_path, size), ...]
        self._last_progress_percent = 0
    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()
        proc = self._proc
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass
    def _stream_reader_to_queue(self, pipe, output_queue: "queue.Queue[str]"):
        """
        Liest stdout/stderr zeichenweise und splittet sowohl auf \\n als auch auf \\r.
        Dadurch kommen auch tqdm-/hf-Fortschrittsupdates an.
        """
        try:
            if pipe is None:
                return
            buf = ""
            while True:
                ch = pipe.read(1)
                if ch == "":
                    if buf.strip():
                        output_queue.put(buf)
                    break
                if ch in ("\n", "\r"):
                    if buf.strip():
                        output_queue.put(buf)
                    buf = ""
                else:
                    buf += ch
        except Exception:
            pass
    def _run_simple_command(self, cmd: List[str], status_text: str):
        self.status_changed.emit(status_text)
        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True,
            creationflags=creationflags
        )
        output_queue = queue.Queue()
        reader_thread = threading.Thread(
            target=self._stream_reader_to_queue,
            args=(self._proc.stdout, output_queue),
            daemon=True
        )
        reader_thread.start()
        while True:
            if self._cancel_requested or self.isInterruptionRequested():
                break
            while True:
                try:
                    line = output_queue.get_nowait()
                except queue.Empty:
                    break
                self._consume_output_line(line)
            ret = self._proc.poll()
            if ret is not None:
                break
            self.msleep(100)
        if self._cancel_requested or self.isInterruptionRequested():
            try:
                self._proc.terminate()
            except Exception:
                pass
            raise RuntimeError(self._tr("hf_error_cancelled"))
        ret = self._proc.wait()
        if ret != 0:
            raise RuntimeError(f"Befehl wurde mit Exit-Code {ret} beendet:\n{' '.join(cmd)}")
    def _consume_output_line(self, line: str):
        txt = _force_text(line).strip()
        if not txt:
            return
        self._last_status_line = txt
        current_file = self._extract_current_file_from_output(txt)
        if current_file:
            self._current_file = current_file
        # WICHTIG:
        # KEIN Prozentwert aus der hf-Ausgabe direkt für den ProgressBar übernehmen,
        # weil das meist nur der Fortschritt der aktuellen Datei ist
        # und NICHT des gesamten Modell-Downloads.
        if "still waiting to acquire lock" in txt.lower():
            self.status_changed.emit(self._tr("hf_status_waiting_for_lock"))
        else:
            self.status_changed.emit(txt)
    def _sum_downloaded_bytes(self, folder: str) -> int:
        total = 0
        if not os.path.isdir(folder):
            return 0
        for root, _dirs, files in os.walk(folder):
            for name in files:
                full = os.path.join(root, name)
                # Metadateien ignorieren
                low = name.lower()
                if low.endswith(".lock"):
                    continue
                if low in {".gitattributes", "refs", "snapshots"}:
                    continue
                try:
                    total += os.path.getsize(full)
                except Exception:
                    pass
        return total
    def _fetch_repo_files(self) -> List[Tuple[str, int]]:
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            info = api.model_info(self.repo_id, files_metadata=True)
            out = []
            for sibling in getattr(info, "siblings", []) or []:
                rel = getattr(sibling, "rfilename", None) or getattr(sibling, "path", None)
                size = getattr(sibling, "size", None)
                if not rel or not isinstance(size, int) or size <= 0:
                    continue
                low = str(rel).lower().replace("\\", "/")
                if low.endswith(".lock"):
                    continue
                out.append((str(rel).replace("\\", "/"), int(size)))
            return out
        except Exception:
            return []
    def _repo_total_bytes(self) -> int:
        return sum(size for _rel, size in self._repo_files)
    def _scan_local_progress(self) -> Tuple[int, int, str]:
        """
        Returns:
            downloaded_bytes,
            finished_files_count,
            last_finished_file
        """
        downloaded = 0
        finished = 0
        last_finished = ""
        if not os.path.isdir(self.local_dir):
            return 0, 0, ""
        for rel_path, expected_size in self._repo_files:
            full = os.path.join(self.local_dir, *rel_path.split("/"))
            if not os.path.isfile(full):
                continue
            try:
                size = os.path.getsize(full)
            except Exception:
                continue
            downloaded += size
            if expected_size > 0 and size >= expected_size:
                finished += 1
                last_finished = rel_path
        return downloaded, finished, last_finished
    def _extract_current_file_from_output(self, line: str) -> str:
        txt = (line or "").strip()
        patterns = [
            r"Downloading '([^']+)'",
            r"Download file to .*?[/\\\\]([^/\\\\]+)$",
            r"Fetching (\S+)",
        ]
        for pat in patterns:
            m = re.search(pat, txt, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""
    def run(self):
        try:
            os.makedirs(self.local_dir, exist_ok=True)
            install_cmd = list(self.install_cmd)
            download_cmd = list(self.download_cmd)
            self.progress_changed.emit(0)
            self.status_changed.emit("Ermittle Dateiliste und Gesamtgröße des Modells …")
            self._repo_files = self._fetch_repo_files()
            total_bytes = self._repo_total_bytes()
            total_files = len(self._repo_files)
            start_time = time.time()
            creationflags = 0
            if sys.platform.startswith("win"):
                creationflags = subprocess.CREATE_NO_WINDOW
            # 1) Vorbereitende Befehle (z. B. venv) ausführen
            for cmd in self.prepare_cmds:
                cmd_text = " ".join(cmd).lower()
                if "-m venv" in cmd_text:
                    self._run_simple_command(cmd, "Erzeuge geschützte Python-Umgebung für Whisper …")
                else:
                    self._run_simple_command(cmd, "Bereite Whisper-Umgebung vor …")
            # 2) Requirements installieren
            self._run_simple_command(
                install_cmd,
                "Installiere Python-Requirements für Whisper …"
            )
            # 3) Dateiliste/Gesamtgröße ermitteln
            self.status_changed.emit("Ermittle Dateiliste und Gesamtgröße des Modells …")
            self._repo_files = self._fetch_repo_files()
            total_bytes = self._repo_total_bytes()
            total_files = len(self._repo_files)
            start_time = time.time()
            # 3) Download starten
            self.status_changed.emit("Starte Modell-Download …")
            self._proc = subprocess.Popen(
                download_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True,
                creationflags=creationflags
            )
            output_queue = queue.Queue()
            reader_thread = threading.Thread(
                target=self._stream_reader_to_queue,
                args=(self._proc.stdout, output_queue),
                daemon=True
            )
            reader_thread.start()
            last_emit_ts = 0.0
            while True:
                if self._cancel_requested or self.isInterruptionRequested():
                    break
                while True:
                    try:
                        line = output_queue.get_nowait()
                    except queue.Empty:
                        break
                    self._consume_output_line(line)
                ret = self._proc.poll()
                now = time.time()
                if now - last_emit_ts >= 0.25:
                    downloaded, finished_files, last_finished = self._scan_local_progress()
                    elapsed = max(0.0, now - start_time)
                    if last_finished:
                        self._last_finished_file = last_finished
                    if total_files > 0:
                        percent_tenths = int((finished_files / total_files) * 1000)  # 0.1%-Schritte
                    else:
                        percent_tenths = 0
                    percent_tenths = max(0, min(1000, percent_tenths))
                    self._last_progress_percent = percent_tenths
                    self.progress_changed.emit(percent_tenths)
                    lines = [
                        f"{percent_tenths / 10:.1f}%  |  2,9GB (total)  |  {elapsed:.0f}s (ca. 2-5min)"
                    ]
                    if total_files > 0:
                        lines.append(self._tr("hf_status_files_done", finished_files, total_files))
                    if self._current_file:
                        lines.append(self._tr("hf_status_current_file", self._current_file))
                    if self._last_finished_file:
                        lines.append(self._tr("hf_status_last_finished", self._last_finished_file))
                    self.status_changed.emit("\n".join(lines))
                else:
                    downloaded_mb = downloaded / (1024 * 1024)
                    speed = (downloaded_mb / elapsed) if elapsed > 0 else 0.0
                    lines = [
                        f"{downloaded_mb:.1f} MB geladen  |  {elapsed:.0f}s  |  {speed:.1f} MB/s"
                    ]
                    if total_files > 0:
                        lines.append(self._tr("hf_status_files_done", finished_files, total_files))
                    if self._current_file:
                        lines.append(self._tr("hf_status_current_file", self._current_file))
                    if self._last_finished_file:
                        lines.append(self._tr("hf_status_last_finished", self._last_finished_file))
                    self.status_changed.emit("\n".join(lines))
                if ret is not None:
                    break
                self.msleep(100)
            if self._cancel_requested or self.isInterruptionRequested():
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                raise RuntimeError(self._tr("hf_error_cancelled"))
            ret = self._proc.wait()
            if ret != 0:
                raise RuntimeError(self._tr("hf_error_hf_exit", ret))
            self.progress_changed.emit(1000)
            self.status_changed.emit(self._tr("hf_status_download_done"))
            self.finished_download.emit(self.local_dir)
        except FileNotFoundError:
            self.failed_download.emit(self._tr("hf_error_python_missing"))
        except Exception as e:
            msg = str(e)
            low = msg.lower()
            if "externally-managed-environment" in low:
                msg = self._tr("hf_error_externally_managed")
            elif "no module named venv" in low or "ensurepip" in low:
                msg = self._tr("hf_error_no_venv")
            elif "no such file or directory" in low and "python3" in low:
                msg = self._tr("hf_error_python3_missing")
            self.failed_download.emit(msg)
        finally:
            self._proc = None
