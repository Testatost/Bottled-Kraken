"""Photoshop-ähnliche Mesh-Verkrümmung für die Bildbearbeitung."""
from ..shared import *


def default_warp_grid(x1: float, y1: float, x2: float, y2: float):
    cx = (float(x1) + float(x2)) / 2.0
    cy = (float(y1) + float(y2)) / 2.0
    return [(x1, y1), (cx, y1), (x2, y1), (x1, cy), (cx, cy), (x2, cy), (x1, y2), (cx, y2), (x2, y2)]


def _bilinear_point(c00, c10, c11, c01, u: float, v: float):
    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, float(v)))
    x = (
        (1.0 - u) * (1.0 - v) * float(c00[0])
        + u * (1.0 - v) * float(c10[0])
        + u * v * float(c11[0])
        + (1.0 - u) * v * float(c01[0])
    )
    y = (
        (1.0 - u) * (1.0 - v) * float(c00[1])
        + u * (1.0 - v) * float(c10[1])
        + u * v * float(c11[1])
        + (1.0 - u) * v * float(c01[1])
    )
    return (x, y)


def _grid_point(grid, col: int, row: int):
    col = max(0, min(2, int(col)))
    row = max(0, min(2, int(row)))
    return grid[row * 3 + col]


def _lagrange_basis_3(t: float):
    t = max(0.0, min(1.0, float(t)))
    return (
        2.0 * (t - 0.5) * (t - 1.0),
        4.0 * t * (1.0 - t),
        2.0 * t * (t - 0.5),
    )


def _lagrange_surface_point(grid, u: float, v: float):
    bu = _lagrange_basis_3(u)
    bv = _lagrange_basis_3(v)
    x = 0.0
    y = 0.0
    for row in range(3):
        for col in range(3):
            w = float(bu[col]) * float(bv[row])
            px, py = _grid_point(grid, col, row)
            x += w * float(px)
            y += w * float(py)
    return (x, y)




def _lagrange_basis_5(t: float):
    t = max(0.0, min(1.0, float(t)))
    nodes = (0.0, 0.25, 0.5, 0.75, 1.0)
    basis = []
    for i, xi in enumerate(nodes):
        num = 1.0
        den = 1.0
        for j, xj in enumerate(nodes):
            if i == j:
                continue
            num *= (t - xj)
            den *= (xi - xj)
        basis.append(num / den if abs(den) > 1e-12 else 0.0)
    return tuple(basis)


def _grid_point_5(grid, col: int, row: int):
    col = max(0, min(4, int(col)))
    row = max(0, min(4, int(row)))
    return grid[row * 5 + col]


def _lagrange_surface_point_5(grid, u: float, v: float):
    bu = _lagrange_basis_5(u)
    bv = _lagrange_basis_5(v)
    x = 0.0
    y = 0.0
    for row in range(5):
        for col in range(5):
            w = float(bu[col]) * float(bv[row])
            px, py = _grid_point_5(grid, col, row)
            x += w * float(px)
            y += w * float(py)
    return (x, y)


def _piecewise_bilinear_surface_point_5(grid, u: float, v: float):
    """Lokaler 5x5-Mesh-Warp.

    Im UI hat der Warp ein festes Randgitter und 9 innere Kontrollpunkte.
    Die alte globale Lagrange-Interpolation ließ beim Ziehen eines einzelnen
    inneren Punkts auch weit entfernte Bereiche sichtbar mitziehen. Für die
    Bildbearbeitung ist das unerwünscht: ein innerer Punkt soll nur die
    unmittelbar angrenzenden vier Mesh-Zellen beeinflussen, während der Rand
    stabil bleibt, solange keine Randgriffe bewegt werden.
    """
    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, float(v)))
    div = 4
    col = min(div - 1, max(0, int(math.floor(u * div))))
    row = min(div - 1, max(0, int(math.floor(v * div))))
    local_u = (u - (col / div)) * div
    local_v = (v - (row / div)) * div
    p00 = _grid_point_5(grid, col, row)
    p10 = _grid_point_5(grid, col + 1, row)
    p11 = _grid_point_5(grid, col + 1, row + 1)
    p01 = _grid_point_5(grid, col, row + 1)
    return _bilinear_point(p00, p10, p11, p01, local_u, local_v)

def warp_map_uv(grid, u: float, v: float):
    if not grid or len(grid) not in (9, 25):
        return (0.0, 0.0)

    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, float(v)))

    # 9-Punkt-Gitter bleiben rückwärtskompatibel für alte Zustände.
    # Das neue 25-Punkt-Gitter wird bewusst lokal stückweise bilinear
    # interpoliert: ein verschobener innerer Punkt beeinflusst nur seine
    # Nachbarzellen und zieht nicht global entfernte Bildbereiche mit.
    if len(grid) == 25:
        return _piecewise_bilinear_surface_point_5(grid, u, v)
    return _lagrange_surface_point(grid, u, v)


def warp_map_rect_point(src_rect, grid, x: float, y: float):
    x1, y1, x2, y2 = src_rect
    u = (float(x) - float(x1)) / max(1.0, float(x2) - float(x1))
    v = (float(y) - float(y1)) / max(1.0, float(y2) - float(y1))
    return warp_map_uv(grid, u, v)


def scale_grid(grid, sx: float, sy: float):
    return [(float(x) * float(sx), float(y) * float(sy)) for x, y in (grid or [])]


def _perspective_coefficients(dst_points, src_points):
    matrix = []
    vector = []
    for (xd, yd), (xs, ys) in zip(dst_points, src_points):
        matrix.append([xd, yd, 1, 0, 0, 0, -xs * xd, -xs * yd])
        vector.append(xs)
        matrix.append([0, 0, 0, xd, yd, 1, -ys * xd, -ys * yd])
        vector.append(ys)
    try:
        coeffs = np.linalg.solve(np.array(matrix, dtype=float), np.array(vector, dtype=float))
        return tuple(float(v) for v in coeffs)
    except Exception:
        return None


def _cell_src_quad(w: int, h: int, col: int, row: int, div: int):
    x0 = float(col) * float(w) / float(div)
    x1 = float(col + 1) * float(w) / float(div)
    y0 = float(row) * float(h) / float(div)
    y1 = float(row + 1) * float(h) / float(div)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _grid_is_identity(src_rect, grid, eps: float = 1e-6) -> bool:
    if not grid or len(grid) not in (9, 25):
        return False
    try:
        if len(grid) == 9:
            default = default_warp_grid(*src_rect)
        else:
            x1, y1, x2, y2 = [float(v) for v in src_rect]
            default = []
            for row in range(5):
                v = row / 4.0
                for col in range(5):
                    u = col / 4.0
                    default.append((x1 + (x2 - x1) * u, y1 + (y2 - y1) * v))
        for (gx, gy), (dx, dy) in zip(grid, default):
            if abs(float(gx) - float(dx)) > eps or abs(float(gy) - float(dy)) > eps:
                return False
        return True
    except Exception:
        return False


def _warp_render_division(w: int, h: int) -> int:
    # 20 bleibt der Qualitätswert für Photoshop-ähnliche Glätte. Sehr kleine
    # Ausschnitte brauchen aber nicht unnötig viele Teiltransformationen.
    longest = max(int(w), int(h))
    if longest < 220:
        return 12
    if longest < 520:
        return 16
    return 20


def _quad_bbox_rel(points, min_x: int, min_y: int, out_w: int, out_h: int):
    xs = [float(x) - float(min_x) for x, _ in points]
    ys = [float(y) - float(min_y) for _, y in points]
    bx0 = max(0, int(math.floor(min(xs))) - 1)
    by0 = max(0, int(math.floor(min(ys))) - 1)
    bx1 = min(int(out_w), int(math.ceil(max(xs))) + 2)
    by1 = min(int(out_h), int(math.ceil(max(ys))) + 2)
    if bx1 - bx0 < 1 or by1 - by0 < 1:
        return None
    return bx0, by0, bx1, by1


def _warp_cell_to_local_bbox(crop: Image.Image, out_size, dst_abs, src_quad, min_x: int, min_y: int, perspective_mode=None):
    bbox = _quad_bbox_rel(dst_abs, min_x, min_y, out_size[0], out_size[1])
    if bbox is None:
        return None
    bx0, by0, bx1, by1 = bbox
    local_size = (bx1 - bx0, by1 - by0)
    dst_local = [
        (float(x) - float(min_x) - float(bx0), float(y) - float(min_y) - float(by0))
        for x, y in dst_abs
    ]
    coeffs = _perspective_coefficients(dst_local, src_quad)
    if coeffs is None:
        return None
    if perspective_mode is None:
        perspective_mode = Image.PERSPECTIVE
    cell = crop.transform(
        local_size,
        perspective_mode,
        coeffs,
        resample=Image.BICUBIC,
        fillcolor=(255, 255, 255, 0),
    ).convert("RGBA")
    mask = Image.new("L", local_size, 0)
    ImageDraw.Draw(mask).polygon(dst_local, fill=255)
    alpha = np.minimum(
        np.asarray(cell.getchannel("A"), dtype=np.uint8),
        np.asarray(mask, dtype=np.uint8),
    )
    cell.putalpha(Image.fromarray(alpha, "L"))
    return cell, bx0, by0


def warp_rgba_by_grid(crop_rgba: Image.Image, src_rect, grid, bounds=None):
    crop = crop_rgba.convert("RGBA")
    w, h = crop.size
    if w < 2 or h < 2:
        return crop, int(src_rect[0]), int(src_rect[1])
    if not grid or len(grid) not in (9, 25):
        grid = default_warp_grid(*src_rect)
    if _grid_is_identity(src_rect, grid):
        return crop, int(src_rect[0]), int(src_rect[1])

    xs = [float(x) for x, _ in grid]
    ys = [float(y) for _, y in grid]
    min_x = int(math.floor(min(xs)))
    min_y = int(math.floor(min(ys)))
    max_x = int(math.ceil(max(xs)))
    max_y = int(math.ceil(max(ys)))
    if bounds is not None:
        min_x = max(0, min_x)
        min_y = max(0, min_y)
        max_x = min(int(bounds[0]), max_x)
        max_y = min(int(bounds[1]), max_y)
    if max_x - min_x < 2 or max_y - min_y < 2:
        return crop, int(src_rect[0]), int(src_rect[1])

    out_size = (max_x - min_x, max_y - min_y)
    result = Image.new("RGBA", out_size, (255, 255, 255, 0))
    div = 20
    div = max(18, min(24, _warp_render_division(w, h) if max(int(w), int(h)) >= 220 else div))
    perspective_mode = Image.PERSPECTIVE

    # Wichtig für große Auswahlen:
    # Jede Mesh-Zelle wird nur noch in ihrer eigenen kleinen Ziel-Bounding-Box
    # transformiert. Die alte Variante transformierte pro Zelle die komplette
    # Ausgabegröße und war deshalb bei großen Auswahlbereichen extrem langsam.
    for row in range(div):
        for col in range(div):
            u0, u1 = col / div, (col + 1) / div
            v0, v1 = row / div, (row + 1) / div
            dst = [
                warp_map_uv(grid, u0, v0),
                warp_map_uv(grid, u1, v0),
                warp_map_uv(grid, u1, v1),
                warp_map_uv(grid, u0, v1),
            ]
            warped = _warp_cell_to_local_bbox(
                crop,
                out_size,
                dst,
                _cell_src_quad(w, h, col, row, div),
                min_x,
                min_y,
                perspective_mode,
            )
            if warped is None:
                continue
            cell, bx0, by0 = warped
            result.alpha_composite(cell, (bx0, by0))
    return result, min_x, min_y


def legacy_sine_warp_rgba(crop: Image.Image, warp_x: float = 0.0, warp_y: float = 0.0) -> Image.Image:
    original_mode = getattr(crop, "mode", "RGB")
    try:
        keep_alpha = "A" in str(original_mode)
        work_mode = "RGBA" if keep_alpha else "RGB"
        crop = crop.convert(work_mode)
        w, h = crop.size
        if w < 2 or h < 2:
            return crop
        arr = np.asarray(crop, dtype=np.float32)
        yy, xx = np.indices((h, w), dtype=np.float32)
        src_x = xx - float(warp_x) * np.sin(np.pi * yy / max(1.0, h - 1.0))
        src_y = yy - float(warp_y) * np.sin(np.pi * xx / max(1.0, w - 1.0))
        valid = (src_x >= 0.0) & (src_x <= (w - 1)) & (src_y >= 0.0) & (src_y <= (h - 1))
        src_x = np.clip(src_x, 0, w - 1); src_y = np.clip(src_y, 0, h - 1)
        x0 = np.floor(src_x).astype(np.int32); y0 = np.floor(src_y).astype(np.int32)
        x1 = np.clip(x0 + 1, 0, w - 1); y1 = np.clip(y0 + 1, 0, h - 1)
        dx = (src_x - x0)[..., None]; dy = (src_y - y0)[..., None]
        top = arr[y0, x0] * (1.0 - dx) + arr[y0, x1] * dx
        bottom = arr[y1, x0] * (1.0 - dx) + arr[y1, x1] * dx
        out = top * (1.0 - dy) + bottom * dy
        out[~valid] = np.array([255, 255, 255, 0] if keep_alpha else [255, 255, 255], dtype=np.float32)
        result = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), work_mode)
        return result.convert(original_mode) if keep_alpha and original_mode != work_mode else result
    except Exception:
        return crop
