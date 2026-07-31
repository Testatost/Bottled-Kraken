from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())

import copy
import hashlib


def _bk_lm_transcription_image_urls(payload: dict):
    out = []
    if not isinstance(payload, dict):
        return out
    for message in payload.get("messages", []) or []:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "image_url":
                continue
            image_url = item.get("image_url")
            if isinstance(image_url, dict):
                url = image_url.get("url")
            else:
                url = image_url
            if isinstance(url, str) and url:
                out.append(url)
    return out


def _bk_lm_transcription_url_fingerprint(url: str) -> str:
    return hashlib.sha256(str(url or "").encode("utf-8", errors="ignore")).hexdigest()


def _bk_lm_transcription_replace_image_url(payload: dict, old_url: str, new_url: str) -> dict:
    cloned = copy.deepcopy(payload)
    for message in cloned.get("messages", []) or []:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "image_url":
                continue
            image_url = item.get("image_url")
            if isinstance(image_url, dict):
                if image_url.get("url") == old_url:
                    image_url["url"] = new_url
            elif image_url == old_url:
                item["image_url"] = {"url": new_url}
    return cloned


try:
    _BK_LM_TRANSCRIPTION_PREV_POST_JSON = AIRevisionWorker._post_json
except Exception:
    _BK_LM_TRANSCRIPTION_PREV_POST_JSON = None


def _bk_lm_transcription_guarded_post_json(self, payload: dict):
    """Guarantee one optional page image request, then overlay-crop images only.

    During normal line transcription, any image-bearing request outside the
    optional context step must use the exact active overlay crop. If an older
    wrapper accidentally supplies the page image (or any other image), the guard
    replaces it with the active crop before the HTTP request is sent.
    """
    if not getattr(self, "_bk_strict_overlay_transcription_active", False):
        return _BK_LM_TRANSCRIPTION_PREV_POST_JSON(self, payload)

    image_urls = _bk_lm_transcription_image_urls(payload)
    if not image_urls:
        return _BK_LM_TRANSCRIPTION_PREV_POST_JSON(self, payload)

    context_active = bool(getattr(self, "_bk_full_page_context_request_active", False))
    if context_active:
        page_requests = int(getattr(self, "_bk_full_page_context_post_count", 0) or 0)
        if page_requests >= 1:
            raise RuntimeError(
                "Repeated full-page LM image request blocked: the page image may only be sent once as context."
            )
        self._bk_full_page_context_post_count = page_requests + 1
        return _BK_LM_TRANSCRIPTION_PREV_POST_JSON(self, payload)

    active_crop = getattr(self, "_bk_active_overlay_crop_data_url", None)
    if not active_crop:
        raise RuntimeError(
            "Image request blocked during line transcription: no active overlay crop is available."
        )

    guarded_payload = payload
    for image_url in image_urls:
        if image_url == active_crop:
            continue
        guarded_payload = _bk_lm_transcription_replace_image_url(
            guarded_payload,
            image_url,
            active_crop,
        )

    return _BK_LM_TRANSCRIPTION_PREV_POST_JSON(self, guarded_payload)


if callable(_BK_LM_TRANSCRIPTION_PREV_POST_JSON):
    AIRevisionWorker._post_json = _bk_lm_transcription_guarded_post_json


__all__ = [
    '_bk_lm_transcription_guarded_post_json',
    '_bk_lm_transcription_image_urls',
    '_bk_lm_transcription_replace_image_url',
    '_bk_lm_transcription_url_fingerprint',
]
register_globals('bk', globals(), __all__)
