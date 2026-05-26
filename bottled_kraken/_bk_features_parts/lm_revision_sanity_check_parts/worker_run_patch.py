def _bk_fix50_ai_revision_run(self):
    if isinstance(self, BKFullPageLMOCRWorker):
        try:
            return _BK_FIX41_PREV_AI_RUN(self) if callable(globals().get('_BK_FIX41_PREV_AI_RUN')) else AIRevisionRuntimeMixin.run(self)
        except Exception:
            return AIRevisionRuntimeMixin.run(self)
    if self._cancelled or self.isInterruptionRequested():
        self.failed_revision.emit(self.path, self._tr('msg_ai_cancelled'))
        return
    try:
        if not self.recs:
            self.finished_revision.emit(self.path, [])
            return
        total = max(1, len(self.recs))
        original_lines = [_bk_fix50_norm_space(getattr(rv, 'text', '') or '') for rv in self.recs]

        # 1) Echter LM-Seiten-OCR. Anders als vorher ist das nicht nur Kontext,
        # sondern liefert eine pro Zielzeile ausgerichtete dritte OCR-Quelle.
        page_lines = _bk_fix46_get_page_context(self)
        full_page_context_text = '\n'.join([_bk_fix50_norm_space(x) for x in page_lines if _bk_fix50_norm_space(x)])

        final_lines: List[str] = []
        for i, rv in enumerate(self.recs):
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_ai_cancelled'))
            self.status_changed.emit(self._tr('ai_status_fix46_overlay_line', i + 1, total, os.path.basename(self.path)))
            kraken_text = original_lines[i] if i < len(original_lines) else _bk_fix50_norm_space(getattr(rv, 'text', '') or '')
            page_line_text = _bk_fix50_find_page_line_candidate(self, rv, kraken_text, page_lines, i)
            try:
                lm_box_text = _bk_fix50_request_overlay_box_revision(self, rv, page_lines, i, total)
            except Exception as exc:
                try:
                    print(f'FIX8.50 overlay-box OCR failed line {i}: {exc}')
                except Exception:
                    pass
                lm_box_text = page_line_text or kraken_text
            prev_final = final_lines[-1] if final_lines else ''
            best = _bk_fix50_sanity_merge_line(
                self,
                kraken_text,
                lm_box_text,
                page_line_text,
                prev_final,
                full_page_context_text,
                page_index_aligned=True,
            )
            final_lines.append(best or kraken_text)
            self.progress_changed.emit(10 + int(((i + 1) / total) * 86))

        try:
            tmp_recs = [RecordView(i, final_lines[i], self.recs[i].bbox) for i in range(len(final_lines))]
            tmp_recs = _bk_fix43_resolve_ditto_marks_in_recs(tmp_recs)
            final_lines = [_bk_fix50_norm_space(getattr(rv, 'text', '') or '') for rv in tmp_recs]
        except Exception:
            final_lines = _bk_fix43_resolve_ditto_marks_in_lines(final_lines)

        if len(final_lines) != len(self.recs):
            raise ValueError(self._tr('ai_err_final_merge_count', len(final_lines), len(self.recs)))
        self.status_changed.emit(self._tr('ai_status_done', os.path.basename(self.path)))
        self.progress_changed.emit(100)
        self.finished_revision.emit(self.path, final_lines)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8', errors='replace')
        except Exception:
            body = str(e)
        self.failed_revision.emit(self.path, self._tr('err_http_with_body', e, body))
    except urllib.error.URLError as e:
        self.failed_revision.emit(self.path, self._tr('ai_err_server_unreachable', e))
    except socket.timeout:
        self.failed_revision.emit(self.path, self._tr('ai_err_timeout'))
    except RuntimeError as e:
        self.failed_revision.emit(self.path, str(e))
    except Exception as e:
        self.failed_revision.emit(self.path, ''.join(traceback.format_exception(type(e), e, e.__traceback__)))

try:
    AIRevisionWorker.run = _bk_fix50_ai_revision_run
    AIRevisionWorker._choose_final_line_text = lambda self, kraken_text, box_text, page_text, prev_final_text='': _bk_fix50_sanity_merge_line(self, kraken_text, box_text, page_text, prev_final_text, page_text, True)
    AIRevisionWorker._request_line_decision = lambda self, idx, kraken_text, page_text, box_text: _bk_fix50_sanity_merge_line(self, kraken_text, box_text, page_text, '', page_text, True)
except Exception:
    pass
