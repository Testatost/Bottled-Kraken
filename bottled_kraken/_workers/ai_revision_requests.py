"""Anfrage-Methoden für den AI-Revision-Worker."""
from ..shared import *

class AIRevisionRequestsMixin:
    def _request_page_ocr_with_fixed_linecount(self, page_data_url: str, recs: List[RecordView]) -> List[str]:
        img_w, img_h = _load_image_color(self.path).size
        line_specs = []
        for rv in recs:
            line_specs.append({
                "idx": int(rv.idx),
                "bbox": _normalize_bbox(rv.bbox, img_w, img_h)
            })
        system_prompt = self._tr("ai_prompt_page_system")
        user_prompt = self._tr(
            "ai_prompt_page_user",
            len(recs),
            len(recs),
            len(recs) - 1,
            json.dumps(line_specs, ensure_ascii=False)
        )

        def _extract_out_lines(content: str):
            obj = _extract_json_payload(content)
            if not isinstance(obj, dict):
                return None
            lines = obj.get("lines")
            if not isinstance(lines, list):
                return None
            out = [""] * len(recs)
            for item in lines:
                if not isinstance(item, dict):
                    continue
                idx = item.get("idx")
                txt = _force_text(item.get("text", "")).strip()
                if isinstance(idx, int) and 0 <= idx < len(recs):
                    out[idx] = txt
            return out

        max_tokens_candidates = []
        primary_tokens = self._effective_revision_max_tokens("page", len(recs))
        max_tokens_candidates.append(primary_tokens)
        retry_tokens = min(12000, max(primary_tokens * 2, 2400, 180 * len(recs) + 600))
        if retry_tokens not in max_tokens_candidates:
            max_tokens_candidates.append(retry_tokens)

        last_content = ""
        last_data = None
        for attempt_no, max_tokens in enumerate(max_tokens_candidates, start=1):
            payload = {
                "model": self.lm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": page_data_url}},
                        ],
                    },
                ],
                **self._build_sampling_payload(
                    response_format=self._response_format_lines(),
                    override_max_tokens=max_tokens,
                ),
            }
            data = self._post_json(payload)
            last_data = data
            try:
                print("RAW FULL LM STUDIO RESPONSE:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:12000])
            except Exception:
                pass
            content = self._extract_message_content(data)
            last_content = content
            try:
                print(f"RAW PAGE OCR RESPONSE (attempt {attempt_no}, max_tokens={max_tokens}):")
                print(content[:4000])
            except Exception:
                pass
            out = _extract_out_lines(content)
            if out is not None:
                filled = sum(1 for x in out if str(x).strip())
                too_long_blocks = sum(1 for x in out if len(str(x).strip()) > 120)
                if too_long_blocks >= 1:
                    raise ValueError(self._tr("ai_err_page_long_blocks"))
                if filled == 0:
                    raise ValueError(self._tr("ai_err_page_no_usable_lines", filled, len(recs)))
                for i in range(len(out)):
                    if not str(out[i]).strip():
                        out[i] = recs[i].text
                return out
            finish_reason = ""
            try:
                choices = data.get("choices") if isinstance(data, dict) else None
                if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                    finish_reason = str(choices[0].get("finish_reason", "")).strip().lower()
            except Exception:
                finish_reason = ""
            looks_truncated = (
                finish_reason == "length"
                or (content or "").count("{") > (content or "").count("}")
                or '"lines"' in (content or "")
            )
            if attempt_no >= len(max_tokens_candidates) or not looks_truncated:
                break

        if isinstance(last_data, dict):
            lines = None
            try:
                choices = last_data.get("choices")
                if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                    finish_reason = str(choices[0].get("finish_reason", "")).strip().lower()
                    if finish_reason == "length":
                        raise ValueError(
                            self._tr("ai_err_page_invalid_json", (last_content[:2600] + "\n\n[Hinweis: Modellantwort wurde wahrscheinlich wegen max_tokens abgeschnitten.]") if last_content else "<leer>")
                        )
            except ValueError:
                raise
            except Exception:
                pass
        raise ValueError(
            self._tr("ai_err_page_invalid_json", last_content[:3000] if last_content else "<leer>")
        )

    def _request_single_line_reread(
            self,
            line_data_url: str,
            idx: int,
            current_text: str = "",
    ) -> str:
        system_prompt = self._tr("ai_prompt_single_system")
        user_prompt = self._tr("ai_prompt_single_user", idx)
        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": line_data_url}},
                    ],
                },
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_single_text(),
                override_max_tokens=self._effective_revision_max_tokens("single", 1)
            ),
        }
        data = self._post_json(payload)
        content = self._extract_message_content(data)
        try:
            print("RAW SINGLE LINE RESPONSE:")
            print(content[:2000])
        except Exception:
            pass
        if "```" in content:
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        content = content.strip()
        obj = None
        try:
            obj = json.loads(content)
        except Exception:
            pass
        if obj is None:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    obj = json.loads(content[start:end + 1])
                except Exception:
                    pass
        if isinstance(obj, dict):
            txt = _force_text(obj.get("text", "")).strip()
            if txt or txt == "":
                return txt
        lines = _extract_text_lines(content)
        if lines:
            return lines[0].strip()
        return ""

    def _request_line_decision(
            self,
            idx: int,
            kraken_text: str,
            page_text: str,
            box_text: str,
    ) -> str:
        system_prompt = self._tr("ai_prompt_decision_system")
        user_prompt = self._tr(
            "ai_prompt_decision_user",
            idx,
            kraken_text,
            page_text,
            box_text
        )
        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_single_text(),
                override_max_tokens=self._effective_revision_max_tokens("decision", 1)
            ),
        }
        data = self._post_json(payload)
        content = self._extract_message_content(data)
        try:
            print("RAW LINE DECISION RESPONSE:")
            print(content[:2000])
        except Exception:
            pass
        if "```" in content:
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        content = content.strip()
        obj = None
        try:
            obj = json.loads(content)
        except Exception:
            pass
        if obj is None:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    obj = json.loads(content[start:end + 1])
                except Exception:
                    pass
        if isinstance(obj, dict):
            txt = _force_text(obj.get("text", "")).strip()
            if txt:
                return txt
        lines = _extract_text_lines(content)
        if lines:
            return lines[0].strip()
        # sehr konservativer Fallback:
        # BOX > KRAKEN > PAGE
        if _force_text(box_text).strip():
            return _force_text(box_text).strip()
        if _force_text(kraken_text).strip():
            return _force_text(kraken_text).strip()
        return _force_text(page_text).strip()

    def _effective_revision_max_tokens(self, request_kind: str = "generic", item_count: int = 1) -> int:
        requested = max(1, int(self.max_tokens or 0))
        item_count = max(1, int(item_count or 1))
        if request_kind == "single":
            cap = 220
            return min(requested, cap)
        if request_kind == "decision":
            cap = 220
            return min(requested, cap)
        if request_kind == "block":
            hard_cap = 3200
            recommended = min(hard_cap, max(700, 240 * item_count + 120))
            return min(max(requested, recommended), hard_cap)
        if request_kind == "page":
            hard_cap = 12000
            recommended = min(hard_cap, max(2400, 180 * item_count + 600))
            return min(max(requested, recommended), hard_cap)
        cap = 1200
        return min(requested, cap)

    def _build_sampling_payload(self, response_format: Optional[dict] = None, override_max_tokens: Optional[int] = None) -> dict:
        payload = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "max_tokens": max(1, int(override_max_tokens if override_max_tokens is not None else self.max_tokens)),
            "stream": False,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if self.top_k > 0:
            payload["top_k"] = self.top_k
        if self.min_p > 0:
            payload["min_p"] = self.min_p
        if self.repetition_penalty != 1.0:
            payload["repetition_penalty"] = self.repetition_penalty
        return payload

    def _response_format_lines(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ocr_lines",
                "schema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "idx": {"type": "integer"},
                                    "text": {"type": "string"}
                                },
                                "required": ["idx", "text"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["lines"],
                    "additionalProperties": False
                }
            }
        }

    def _response_format_single_text(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ocr_single_line",
                "schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"],
                    "additionalProperties": False
                }
            }
        }

    def _normalize_lines(self, revised: list, original: list) -> list:
        revised = [str(x).strip() for x in revised]
        if len(revised) == len(original):
            return revised
        if len(revised) > len(original):
            return revised[:len(original)]
        fixed = list(revised)
        fixed.extend(original[len(revised):])
        return fixed

    def _post_json(self, payload: dict) -> dict:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        body = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(self.endpoint)
        if parsed.scheme not in ("http", "https"):
            raise RuntimeError(self._tr("ai_err_bad_scheme", parsed.scheme))
        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        if not host:
            raise RuntimeError(self._tr("ai_err_invalid_endpoint"))
        conn = None
        try:
            if parsed.scheme == "https":
                conn = http.client.HTTPSConnection(host, port or 443, timeout=600)
            else:
                conn = http.client.HTTPConnection(host, port or 80, timeout=600)
            self._active_conn = conn
            conn.request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer lm-studio"
                }
            )
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            resp = conn.getresponse()
            raw = resp.read().decode("utf-8", errors="replace")
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            if resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status}: {raw}")
            return json.loads(raw)
        except socket.timeout:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            raise RuntimeError(self._tr("ai_err_timeout"))
        except json.JSONDecodeError as e:
            raise RuntimeError(self._tr("ai_err_invalid_json", e))
        except Exception as e:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            raise
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            if self._active_conn is conn:
                self._active_conn = None
