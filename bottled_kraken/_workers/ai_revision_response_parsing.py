"""Antwortverarbeitung für den AI-Revision-Worker."""
from ..shared import *

class AIRevisionResponseParsingMixin:
    def _extract_message_content(self, data: dict) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(
                f"LM Server lieferte keine choices. Antwort:\n{json.dumps(data, ensure_ascii=False)[:3000]}"
            )
        choice0 = choices[0] or {}
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}
        def flatten(val):
            if val is None:
                return ""
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace").strip()
            if isinstance(val, str):
                return val.strip()
            if isinstance(val, list):
                parts = []
                for part in val:
                    if isinstance(part, bytes):
                        txt = part.decode("utf-8", errors="replace").strip()
                        if txt:
                            parts.append(txt)
                    elif isinstance(part, str) and part.strip():
                        parts.append(part.strip())
                    elif isinstance(part, dict):
                        for key in ("text", "content", "output_text"):
                            v = part.get(key)
                            if isinstance(v, bytes):
                                txt = v.decode("utf-8", errors="replace").strip()
                                if txt:
                                    parts.append(txt)
                            elif isinstance(v, str) and v.strip():
                                parts.append(v.strip())
                return "\n".join(parts).strip()
            if isinstance(val, dict):
                for key in ("text", "content", "output_text"):
                    v = val.get(key)
                    if isinstance(v, bytes):
                        txt = v.decode("utf-8", errors="replace").strip()
                        if txt:
                            return txt
                    elif isinstance(v, str) and v.strip():
                        return v.strip()
            return _force_text(val).strip()
        # 1) ZUERST nur echte Ausgabe lesen
        candidates = []
        if isinstance(message, dict):
            candidates.append(message.get("content"))
            candidates.append(message.get("text"))
            candidates.append(message.get("output_text"))
        if isinstance(choice0, dict):
            candidates.append(choice0.get("content"))
            candidates.append(choice0.get("text"))
        for cand in candidates:
            txt = flatten(cand)
            if txt:
                # <think> entfernen, falls ein Modell sowas trotzdem in content schreibt
                txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL).strip()
                if txt:
                    return txt
        # 2) reasoning_content NICHT als normale Antwort verwenden
        reasoning = ""
        if isinstance(message, dict):
            rc = message.get("reasoning_content")
            if isinstance(rc, str) and rc.strip():
                reasoning = rc.strip()
        finish_reason = ""
        if isinstance(choice0, dict):
            finish_reason = str(choice0.get("finish_reason", "")).strip()
        if reasoning:
            cleaned = re.sub(r"<think>.*?</think>", "", reasoning, flags=re.DOTALL).strip()
            # Falls reasoning_content selbst schon JSON enthält, nutzen wir es als Notfall-Fallback
            if cleaned:
                if cleaned.startswith("{") or '"lines"' in cleaned or '"text"' in cleaned:
                    return cleaned
            if finish_reason == "length":
                raise RuntimeError(
                    self._tr("ai_err_reasoning_truncated")
                )
            raise RuntimeError(
                self._tr("ai_err_reasoning_only")
            )
        raise RuntimeError(self._tr("ai_err_no_content"))

    def _request_block_reread(
            self,
            block_data_url: str,
            start_idx: int,
            end_idx: int,
            current_lines: List[str],
    ) -> List[str]:
        count = end_idx - start_idx
        system_prompt = self._tr("ai_prompt_block_system")
        joined_hint = "\n".join(
            f"{i}: {txt}" for i, txt in enumerate(current_lines)
        )
        user_prompt = self._tr(
            "ai_prompt_block_user",
            count,
            joined_hint
        )
        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": block_data_url}},
                    ],
                },
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_lines(),
                override_max_tokens=self._effective_revision_max_tokens("block", count)
            ),
        }
        data = self._post_json(payload)
        content = self._extract_message_content(data)
        try:
            print("RAW BLOCK RESPONSE:")
            print(content[:3000])
        except Exception:
            pass
        obj = _extract_json_payload(content)
        if not isinstance(obj, dict):
            raise ValueError(
                self._tr("ai_err_block_invalid_json", content[:3000] if content else "<leer>")
            )
        lines = obj.get("lines")
        if not isinstance(lines, list):
            raise ValueError(
                self._tr("ai_err_block_invalid_lines", content[:3000] if content else "<leer>")
            )
        out = [""] * count
        for item in lines:
            if not isinstance(item, dict):
                continue
            idx = item.get("idx")
            txt = _force_text(item.get("text", "")).strip()
            if isinstance(idx, int) and 0 <= idx < count:
                out[idx] = txt
        fixed = []
        for i in range(count):
            txt = out[i].strip()
            fallback = current_lines[i] if i < len(current_lines) else ""
            if txt:
                fixed.append(txt)
            else:
                fixed.append(fallback)
        return fixed

    def _chunk_records(self, recs: List[RecordView], block_size: int = 3) -> List[Tuple[int, int]]:
        chunks: List[Tuple[int, int]] = []
        i = 0
        n = len(recs)
        while i < n:
            j = min(n, i + block_size)
            chunks.append((i, j))
            i = j
        return chunks
