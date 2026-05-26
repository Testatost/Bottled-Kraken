"""Worker-Klassen für Bottled Kraken."""
from ..shared import *

MAX_KRAKEN_OCR_LINES = 500

class PDFRenderWorker(QThread):
    progress = Signal(int, int, str)  # current, total, pdf_path
    finished_pdf = Signal(str, list)  # pdf_path, out_paths
    failed_pdf = Signal(str, str)  # pdf_path, error_message

    @staticmethod
    def _max_render_pixels() -> int:
        # Zielgrenze für temporär gerenderte PDF-Seiten.
        # 80 MP liegt unter der ursprünglichen Pillow-Warnschwelle und verhindert
        # bei sehr großen Scan-PDFs unnötige Warnungen sowie RAM-Spitzen.
        raw = os.environ.get("BOTTLED_KRAKEN_PDF_RENDER_MAX_PIXELS", "80000000")
        try:
            return max(20_000_000, int(raw))
        except Exception:
            return 80_000_000

    @staticmethod
    def _min_render_dpi() -> int:
        raw = os.environ.get("BOTTLED_KRAKEN_PDF_RENDER_MIN_DPI", "180")
        try:
            return max(96, int(raw))
        except Exception:
            return 180

    @classmethod
    def _matrix_for_page(cls, page, requested_dpi: int) -> Tuple[fitz.Matrix, int]:
        dpi = max(72, int(requested_dpi or 300))
        rect = page.rect
        zoom = dpi / 72.0
        estimated_pixels = max(1.0, float(rect.width) * zoom * float(rect.height) * zoom)
        max_pixels = float(cls._max_render_pixels())
        if estimated_pixels > max_pixels:
            scale = math.sqrt(max_pixels / estimated_pixels)
            dpi = max(cls._min_render_dpi(), int(dpi * scale))
            zoom = dpi / 72.0
        return fitz.Matrix(zoom, zoom), dpi

    def __init__(self, pdf_path: str, dpi: int = 300, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.dpi = int(dpi)

    def run(self):
        out_paths: List[str] = []
        try:
            pdf_path = self.pdf_path
            dpi = self.dpi
            base = os.path.splitext(os.path.basename(pdf_path))[0]
            tmp_dir = os.path.join(os.path.dirname(pdf_path), f".kraken_tmp_{base}")
            os.makedirs(tmp_dir, exist_ok=True)
            doc = fitz.open(pdf_path)
            total = int(doc.page_count)
            try:
                for i in range(total):
                    if self.isInterruptionRequested():
                        break
                    page = doc.load_page(i)
                    mat, effective_dpi = self._matrix_for_page(page, dpi)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    out = os.path.join(tmp_dir, f"{base}_p{i + 1:04d}.png")
                    pix.save(out)
                    out_paths.append(out)
                    # MuPDF-Pixmaps explizit freigeben; bei großen PDFs verhindert das Speicheranstieg.
                    pix = None
                    page = None
                    if (i + 1) % 10 == 0:
                        try:
                            gc.collect()
                        except Exception:
                            pass
                    self.progress.emit(i + 1, total, pdf_path)
            finally:
                doc.close()
            # auch wenn abgebrochen -> "fertig" mit dem was da ist
            self.finished_pdf.emit(pdf_path, out_paths)
        except Exception:
            self.failed_pdf.emit(self.pdf_path, traceback.format_exc())
