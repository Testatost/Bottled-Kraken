def _ptr_split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in (text or "").splitlines()]

def _ptr_normalize_line(text: str) -> str:
    txt = (text or "").strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt

def _ptr_pick_best_line(candidates: List[str]) -> str:
    from collections import Counter
    cleaned = [_ptr_normalize_line(x) for x in candidates if _ptr_normalize_line(x)]
    if not cleaned:
        return ""
    counts = Counter(cleaned)
    best_count = max(counts.values())
    best = [line for line, cnt in counts.items() if cnt == best_count]
    if len(best) == 1:
        return best[0]
    best.sort(key=lambda s: (len(s), s))
    return best[-1]

def _ptr_merge_ocr_texts_local(texts: List[str]) -> str:
    prepared: List[List[str]] = []
    for text in texts:
        lines = _ptr_split_lines(text)
        if lines:
            prepared.append(lines)
    if not prepared:
        return ""
    if len(prepared) == 1:
        return "\n".join(prepared[0]).strip()
    max_len = max(len(lines) for lines in prepared)
    merged_lines: List[str] = []
    for i in range(max_len):
        candidates = [lines[i] for lines in prepared if i < len(lines)]
        merged_lines.append(_ptr_pick_best_line(candidates))
    while merged_lines and not merged_lines[-1].strip():
        merged_lines.pop()
    return "\n".join(merged_lines).strip()

def _ptr_build_merge_input_text(ocr_texts: List[str]) -> str:
    parts = []
    for text in ocr_texts:
        cleaned = (text or "").strip()
        if cleaned:
            parts.append(cleaned)
    return f"\n{OCR_SOURCE_SEPARATOR}\n".join(parts) if parts else ""

def _ptr_extract_json_object(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("AI response content is empty.")
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("AI JSON response must be a top-level object.")
        return data
    except json.JSONDecodeError:
        pass
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return _ptr_extract_json_object(fenced_match.group(1).strip())
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start:end + 1]
        try:
            data = json.loads(candidate)
            if not isinstance(data, dict):
                raise ValueError("AI JSON response must be a top-level object.")
            return data
        except json.JSONDecodeError:
            pass
    raise ValueError("Failed to parse JSON object from AI response.")

def _ptr_remote_chat_completion(config: PtrRemoteAIConfig, messages: List[Dict[str, str]],
                                *, expect_json: bool = False,
                                max_tokens: Optional[int] = None) -> Dict[str, Any]:
    base_url = (config.base_url or "").strip()
    if not base_url:
        raise ValueError("Base URL must not be empty.")
    if not re.match(r"^https?://", base_url, flags=re.IGNORECASE):
        raise ValueError("Base URL must start with http:// or https://")
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    payload: Dict[str, Any] = {
        "model": (config.model or "").strip(),
        "messages": messages,
        "temperature": float(config.temperature),
    }
    if not payload["model"]:
        raise ValueError("Model must not be empty.")
    if max_tokens is not None:
        payload["max_tokens"] = int(max_tokens)
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Content-Type": "application/json",
    }
    api_key = (config.api_key or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if (config.provider_name or "").strip().lower() == "openrouter" or "openrouter.ai" in url:
        if (config.app_url or "").strip():
            headers["HTTP-Referer"] = config.app_url.strip()
        if (config.app_name or "").strip():
            headers["X-Title"] = config.app_name.strip()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(5, int(config.timeout_seconds))) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(exc)
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Remote AI request failed: {exc}") from exc
    except socket.timeout as exc:
        raise RuntimeError("Remote AI request timed out.") from exc
    try:
        data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError("Remote AI returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Remote AI returned an unexpected response format.")
    return data

def _ptr_extract_content_from_chat_response(data: Dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Remote AI response contains no choices.")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("Remote AI choice format is invalid.")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("Remote AI message format is invalid.")
    content = message.get("content")
    if isinstance(content, str):
        if content.strip():
            return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        joined = "\n".join(parts).strip()
        if joined:
            return joined
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        finish_reason = first_choice.get("finish_reason")
        if str(finish_reason).lower() == "length":
            raise RuntimeError("The model returned only reasoning_content and was truncated before the final answer. Increase max_tokens or use a non-reasoning model.")
        raise RuntimeError("The model returned only reasoning_content and no usable content.")
    raise RuntimeError("Remote AI response content is empty or unsupported.")
