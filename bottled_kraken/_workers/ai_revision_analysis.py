"""Mixin-Methoden für den AI-Revision-Worker."""
from ..shared import *

class AIRevisionAnalysisMixin:
    def __init__(
            self,
            path: str,
            recs: List[RecordView],
            lm_model: str,
            endpoint: str = "http://127.0.0.1:1234/v1/chat/completions",
            enable_thinking: bool = False,
            source_kind: str = "image",
            script_mode: str = AI_SCRIPT_PRINT,
            temperature: float = 0.2,
            top_p: float = 0.8,
            top_k: int = 10,
            presence_penalty: float = 0.0,
            repetition_penalty: float = 1.0,
            min_p: float = 0.0,
            max_tokens: int = 1200,
            tr_func=None,
            parent=None
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr("de")
        self.path = path
        self.recs = [
            RecordView(i, rv.text, tuple(rv.bbox) if rv.bbox else None)
            for i, rv in enumerate(recs)
        ]
        self._frozen_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in self.recs]
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.source_kind = source_kind
        self.script_mode = _normalize_ai_script_mode(script_mode)
        self.enable_thinking = bool(enable_thinking)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)
        self._cancelled = False
        self._active_conn = None

    def cancel(self):
        self._cancelled = True
        self.requestInterruption()
        conn = self._active_conn
        self._active_conn = None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    def _is_image_processing_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return (
                "failed to process image" in msg
                or "image" in msg and "http 400" in msg
        )

    def _looks_like_form_layout(self) -> bool:
        if not self.recs:
            return False
        short_lines = 0
        empty_or_tiny = 0
        with_bbox = 0
        for rv in self.recs:
            txt = (rv.text or "").strip()
            if rv.bbox:
                with_bbox += 1
            if len(txt) <= 25:
                short_lines += 1
            if len(txt) <= 2:
                empty_or_tiny += 1
        ratio_short = short_lines / max(1, len(self.recs))
        ratio_tiny = empty_or_tiny / max(1, len(self.recs))
        return with_bbox >= max(3, len(self.recs) // 2) and ratio_short >= 0.6 and ratio_tiny >= 0.15

    def _normalize_compare_text(self, text: str) -> str:
        txt = _clean_ocr_text(text or "")
        txt = txt.lower()
        # nur sehr leichte Normalisierung
        txt = txt.replace("ſ", "s")
        txt = txt.replace("ß", "ss")
        # Satzzeichen weitgehend raus, Leerraum glätten
        txt = re.sub(r"[^\w\s]", " ", txt, flags=re.UNICODE)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def _text_similarity_ratio(self, a: str, b: str) -> float:
        import difflib
        aa = self._normalize_compare_text(a)
        bb = self._normalize_compare_text(b)
        if not aa and not bb:
            return 1.0
        if not aa or not bb:
            return 0.0
        return difflib.SequenceMatcher(None, aa, bb).ratio()

    def _token_overlap_ratio(self, a: str, b: str) -> float:
        aa = set(self._normalize_compare_text(a).split())
        bb = set(self._normalize_compare_text(b).split())
        if not aa and not bb:
            return 1.0
        if not aa or not bb:
            return 0.0
        inter = len(aa & bb)
        base = max(1, min(len(aa), len(bb)))
        return inter / base

    def _looks_like_long_block(self, text: str) -> bool:
        txt = _clean_ocr_text(text or "")
        if not txt:
            return False
        # zu lang für eine einzelne Formular-/Kurzzeile
        if len(txt) > 80:
            return True
        # ungewöhnlich viele Wörter -> eher zusammengezogene Nachbarzeilen
        if len(txt.split()) > 12:
            return True
        # explizite Zeilenumbrüche sind hier verdächtig
        if "\n" in txt:
            return True
        return False

    def _is_suspicious_box_result(self, text: str) -> bool:
        txt = _clean_ocr_text(text or "")
        if not txt:
            return True
        if "\n" in txt:
            return True
        if len(txt) <= 2:
            return True
        # typische "komische" OCR-Reste wie KURAVA
        if txt.isupper() and len(txt) >= 5 and " " not in txt:
            return True
        return False

    def _page_text_is_safe_context(
            self,
            kraken_text: str,
            box_text: str,
            page_text: str,
            prev_final_text: str = "",
    ) -> bool:
        pt = _clean_ocr_text(page_text or "")
        bt = _clean_ocr_text(box_text or "")
        kt = _clean_ocr_text(kraken_text or "")
        prev = _clean_ocr_text(prev_final_text or "")
        if not pt:
            return False
        # Niemals lange Blöcke aus Page-OCR übernehmen
        if self._looks_like_long_block(pt):
            return False
        # Niemals Duplikat der vorherigen finalen Zeile erzeugen
        if prev and self._normalize_compare_text(pt) == self._normalize_compare_text(prev):
            return False
        # Page darf nur helfen, wenn es lokal ähnlich genug ist
        sim_box = self._text_similarity_ratio(pt, bt) if bt else 0.0
        sim_kr = self._text_similarity_ratio(pt, kt) if kt else 0.0
        tok_box = self._token_overlap_ratio(pt, bt) if bt else 0.0
        tok_kr = self._token_overlap_ratio(pt, kt) if kt else 0.0
        # sicher nur dann, wenn Page zur lokalen Zeile passt
        if sim_box >= 0.72 or sim_kr >= 0.72:
            return True
        if tok_box >= 0.75 or tok_kr >= 0.75:
            return True
        return False

    def _choose_final_line_text(
            self,
            kraken_text: str,
            box_text: str,
            page_text: str,
            prev_final_text: str = "",
    ) -> str:
        kt = _clean_ocr_text(kraken_text or "")
        bt = _clean_ocr_text(box_text or "")
        pt = _clean_ocr_text(page_text or "")
        # 1) Box ist Primärquelle
        if bt and not self._looks_like_long_block(bt):
            best = bt
        else:
            best = kt
        # 2) Page nur als schwacher Kontext:
        # nur wenn Box leer/fraglich ist UND Page nicht widerspricht
        if self._page_text_is_safe_context(
                kraken_text=kt,
                box_text=bt,
                page_text=pt,
                prev_final_text=prev_final_text,
        ):
            # Nur dann auf Page gehen, wenn Box leer ist
            # oder Box deutlich kürzer/kaputt wirkt als Page,
            # aber Page trotzdem lokal ähnlich genug blieb.
            if not bt:
                best = pt
            else:
                sim_box_kr = self._text_similarity_ratio(bt, kt) if kt else 0.0
                sim_page_kr = self._text_similarity_ratio(pt, kt) if kt else 0.0
                # konservativ: Page nur nehmen, wenn es mindestens so plausibel wie Box wirkt
                if sim_page_kr > sim_box_kr + 0.10 and len(pt) <= len(bt) + 12:
                    best = pt
        # 3) harter Schutz gegen Nachbar-Duplikate
        if prev_final_text:
            if self._normalize_compare_text(best) == self._normalize_compare_text(prev_final_text):
                if kt and self._normalize_compare_text(kt) != self._normalize_compare_text(prev_final_text):
                    best = kt
                elif bt and self._normalize_compare_text(bt) != self._normalize_compare_text(prev_final_text):
                    best = bt
        # 4) niemals leer rausfallen, wenn Kraken was hatte
        if not best:
            best = bt or kt or pt
        return _clean_ocr_text(best)
