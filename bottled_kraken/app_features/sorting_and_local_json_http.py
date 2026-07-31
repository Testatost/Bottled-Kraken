from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
def _bk_local_json_post_json_v21(self, payload: dict) -> dict:
    if self._cancelled or self.isInterruptionRequested():
        raise RuntimeError(self._tr('msg_local_json_cancelled'))
    body = json.dumps(payload).encode('utf-8')
    parsed = urllib.parse.urlparse(self.endpoint)
    if parsed.scheme not in ('http', 'https'):
        raise RuntimeError(self._tr('ai_err_bad_scheme', parsed.scheme))
    host = parsed.hostname
    port = parsed.port
    path = parsed.path or '/'
    if parsed.query:
        path += '?' + parsed.query
    if not host:
        raise RuntimeError(self._tr('ai_err_invalid_endpoint'))
    conn = None
    resp = None
    self._active_conn = None
    self._active_response = None
    self._active_socket = None
    def _refresh_active_socket(c, r=None):
        sock = None
        try:
            sock = getattr(c, 'sock', None)
        except Exception:
            sock = None
        if sock is None and r is not None:
            for attr_chain in (
                ('fp', 'raw', '_sock'),
                ('fp', 'raw', 'sock'),
                ('fp', 'fp', 'raw', '_sock'),
            ):
                try:
                    obj = r
                    for part in attr_chain:
                        obj = getattr(obj, part)
                    if obj is not None:
                        sock = obj
                        break
                except Exception:
                    continue
        self._active_socket = sock
        try:
            if sock is not None:
                sock.settimeout(0.5)
        except Exception:
            pass
    try:
        if parsed.scheme == 'https':
            conn = http.client.HTTPSConnection(host, port or 443, timeout=5)
        else:
            conn = http.client.HTTPConnection(host, port or 80, timeout=5)
        self._active_conn = conn
        conn.connect()
        _refresh_active_socket(conn)
        conn.putrequest('POST', path)
        conn.putheader('Content-Type', 'application/json')
        conn.putheader('Authorization', 'Bearer lm-studio')
        conn.putheader('Connection', 'close')
        conn.putheader('Content-Length', str(len(body)))
        conn.endheaders(body)
        while True:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_local_json_cancelled'))
            try:
                resp = conn.getresponse()
                self._active_response = resp
                _refresh_active_socket(conn, resp)
                break
            except socket.timeout:
                continue
        chunks = []
        while True:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_local_json_cancelled'))
            try:
                chunk = resp.read(65536)
            except socket.timeout:
                continue
            if not chunk:
                break
            chunks.append(chunk)
        raw = b''.join(chunks).decode('utf-8', errors='replace')
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        if resp.status >= 400:
            raise RuntimeError(self._tr('ai_err_http', resp.status, raw))
        return json.loads(raw)
    except socket.timeout:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        raise RuntimeError(self._tr('ai_err_timeout'))
    except json.JSONDecodeError as e:
        raise RuntimeError(self._tr('ai_err_invalid_json', e))
    finally:
        try:
            if resp is not None:
                resp.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        self._active_conn = None
        self._active_response = None
        self._active_socket = None
__all__ = [
    '_bk_local_json_post_json_v21',
]
register_globals('bk', globals(), __all__)
