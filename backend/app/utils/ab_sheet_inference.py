import os
import base64
from typing import Dict, Any, List, Tuple

import cv2
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T

from app.ml.ab_classifier_model import load_trained_model

# Folder for saving debug images (absolute path)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG_CELLS_DIR = os.path.join(_SCRIPT_DIR, "debug_cells")
DEBUG_CROPS_DIR = os.path.join(_SCRIPT_DIR, "debug_crops")
os.makedirs(DEBUG_CELLS_DIR, exist_ok=True)
os.makedirs(DEBUG_CROPS_DIR, exist_ok=True)

SKILL_AREAS = [
    "Gross Motor",
    "Fine Motor",
    "Eating",
    "Dressing",
    "Grooming",
    "Toileting",
    "Receptive Language",
    "Expressive Language",
    "Social Interaction",
    "Reading",
    "Writing",
    "Numbers",
    "Time",
    "Money",
    "Domestic Behaviour",
    "Community Orientation",
    "Recreation",
    "Vocational",
]

HEADERS = [
    "Student Name",
    "Register Number",
    "Skill Area",
    "Session 1", "Session 2", "Session 3", "Session 4", "Session 5",
    "Session 6", "Session 7", "Session 8", "Session 9", "Session 10",
    "Session 11", "Session 12", "Session 13", "Session 14", "Session 15",
    "Session 16", "Session 17", "Session 18", "Session 19", "Session 20",
    "Total A",
    "Total B",
    "I Qr",
    "II Qr",
    "III Qr",
    "IV Qr",
    "Assessment Date",
]

N_ROWS = len(SKILL_AREAS)
N_COLS = 20

WARP_WIDTH = 800
WARP_HEIGHT = 1000

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = None
_MODEL_WEIGHTS_PATH = "app/models/ab_classifier.pth"


def _get_model():
    global _model
    if _model is None:
        _model = load_trained_model(_MODEL_WEIGHTS_PATH, _device)
    return _model


_cell_transform = T.Compose([
    T.Grayscale(num_output_channels=1),
    T.Resize((28, 28)),
    T.ToTensor(),
    T.Normalize(mean=[0.5], std=[0.5]),
])


# ====== IMAGE PIPELINE HELPERS ======

def _bytes_to_bgr(file_bytes: bytes) -> np.ndarray:
    """Decode image bytes into a BGR OpenCV image."""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes")
    return img


def preprocess_image(
    image_bgr: np.ndarray,
    canny_low: int = 50,
    canny_high: int = 150,
    morph_kernel: int = 3,
    dilate_iterations: int = 2,
    erode_iterations: int = 1,
) -> np.ndarray:
    """
    Preprocess image for robust contour detection:
    1) grayscale
    2) Gaussian blur
    3) Canny edge detection
    4) dilation + erosion to strengthen edges
    Returns a binary edge map suitable for contour finding.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)

    k = max(3, morph_kernel)
    if k % 2 == 0:
        k += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))

    strengthened = cv2.dilate(edges, kernel, iterations=max(1, dilate_iterations))
    strengthened = cv2.erode(strengthened, kernel, iterations=max(1, erode_iterations))
    return strengthened


def _preprocess_edges(image_bgr: np.ndarray) -> np.ndarray:
    """Edge-based preprocessing fallback for weak borders or uneven lighting."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    connected = cv2.dilate(edges, kernel, iterations=2)
    connected = cv2.morphologyEx(connected, cv2.MORPH_CLOSE, kernel, iterations=2)
    return connected


def _detect_table_from_grid_lines(image_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Detect table using horizontal+vertical line morphology for this form layout."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        8,
    )
    inv = cv2.bitwise_not(binary)

    h, w = inv.shape[:2]
    h_kernel_len = max(25, w // 20)
    v_kernel_len = max(25, h // 20)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_len, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_len))

    horiz = cv2.morphologyEx(inv, cv2.MORPH_OPEN, h_kernel)
    vert = cv2.morphologyEx(inv, cv2.MORPH_OPEN, v_kernel)

    grid = cv2.addWeighted(horiz, 0.5, vert, 0.5, 0)
    grid = cv2.dilate(grid, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)), iterations=2)
    grid = cv2.morphologyEx(grid, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)), iterations=2)

    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No line-based table contour found")

    image_area = float(h * w)
    best = None
    best_score = -1e9

    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if bh <= 0:
            continue

        width_ratio = bw / float(w)
        height_ratio = bh / float(h)
        x_ratio = x / float(w)
        y_ratio = y / float(h)
        area_ratio = (bw * bh) / image_area
        aspect = bw / float(bh)

        # Tuned for the target sessions table region in this form.
        if width_ratio < 0.42 or width_ratio > 0.78:
            continue
        if height_ratio < 0.25:
            continue
        if aspect < 1.0 or aspect > 2.6:
            continue
        if x_ratio < 0.10 or x_ratio > 0.35:
            continue
        if y_ratio < 0.25:
            continue

        target_x = 0.22
        target_w = 0.56
        score = (
            2.0 * area_ratio
            + 1.6 * width_ratio
            + 0.7 * height_ratio
            - 1.5 * abs(x_ratio - target_x)
            - 0.9 * abs(width_ratio - target_w)
        )
        if score > best_score:
            best_score = score
            best = (x, y, bw, bh, c)

    if best is None:
        raise ValueError("No valid line-based table candidate")

    x, y, bw, bh, contour = best
    pts = np.array(
        [[x, y], [x + bw - 1, y], [x + bw - 1, y + bh - 1], [x, y + bh - 1]],
        dtype=np.float32,
    )
    return contour, pts, grid


def detect_largest_rectangle(
    preprocessed: np.ndarray,
    original_bgr: np.ndarray,
    min_area_ratio: float = 0.02,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect the largest valid 4-sided contour from external contours only.
    Returns:
    - best_contour
    - 4 corner points (float32)
    - visualization of all contours
    - visualization of final selected contour
    """
    contours, _ = cv2.findContours(
        preprocessed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        raise ValueError("No contours found after preprocessing")

    h, w = preprocessed.shape[:2]
    min_area = float(h * w) * float(min_area_ratio)

    all_contours_vis = original_bgr.copy()
    cv2.drawContours(all_contours_vis, contours, -1, (255, 180, 0), 1)

    best_contour = None
    best_points = None
    largest_area = 0.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        # Only accept strict 4-sided candidates.
        if len(approx) != 4:
            continue

        if area > largest_area:
            largest_area = area
            best_contour = contour
            best_points = approx.reshape(4, 2).astype(np.float32)

    if best_points is None:
        raise ValueError("No valid 4-point rectangle contour found")

    final_vis = original_bgr.copy()
    pts_int = best_points.astype(np.int32).reshape((-1, 1, 2))
    cv2.polylines(final_vis, [pts_int], True, (0, 255, 0), 3)

    return best_contour, best_points, all_contours_vis, final_vis


def detect_table(preprocessed: np.ndarray, min_area_ratio: float = 0.03) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect the full assessment table region from external contours.
    Uses geometry constraints to avoid selecting narrow inner sub-regions.
    """
    contours, _ = cv2.findContours(
        preprocessed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        raise ValueError("No contours found in preprocessed image")

    image_h, image_w = preprocessed.shape[:2]
    image_area = float(image_h * image_w)
    min_area = image_area * min_area_ratio

    candidates: List[Tuple[float, np.ndarray, np.ndarray]] = []

    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        perimeter = cv2.arcLength(contour, True)
        polys: List[np.ndarray] = []

        for eps_ratio in (0.015, 0.02, 0.03, 0.04):
            approx = cv2.approxPolyDP(contour, eps_ratio * perimeter, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                polys.append(approx.reshape(4, 2).astype(np.float32))

        rect = cv2.minAreaRect(contour)
        polys.append(cv2.boxPoints(rect).astype(np.float32))

        for poly in polys:
            rect_pts = order_points(poly)
            x, y, w, h = cv2.boundingRect(rect_pts.astype(np.int32))
            if h <= 0:
                continue

            width_ratio = float(w) / image_w
            height_ratio = float(h) / image_h
            x_ratio = float(x) / image_w
            area_ratio = float(w * h) / image_area
            aspect_ratio = float(w) / float(h)

            top_tilt = abs(float(rect_pts[1][1] - rect_pts[0][1])) / max(1.0, float(w))
            bottom_tilt = abs(float(rect_pts[2][1] - rect_pts[3][1])) / max(1.0, float(w))
            tilt = max(top_tilt, bottom_tilt)

            # Hard filters: reject narrow/shifted/over-tilted candidates.
            if width_ratio < 0.55:
                continue
            if height_ratio < 0.25:
                continue
            if aspect_ratio < 1.4:
                continue
            if x_ratio > 0.18:
                continue
            if tilt > 0.16:
                continue

            score = (
                2.0 * area_ratio
                + 1.5 * width_ratio
                + 0.7 * height_ratio
                + 0.8 * (1.0 - min(x_ratio, 1.0))
                + 0.6 * (1.0 - min(tilt, 1.0))
            )
            candidates.append((score, contour, rect_pts))

    if candidates:
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1], candidates[0][2]

    raise ValueError("No valid table contour found for target region")

def order_points(pts: np.ndarray) -> np.ndarray:
    """Order points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def _template_roi_points(image_bgr: np.ndarray) -> np.ndarray:
    """Return calibrated A/B grid ROI points for this assessment form layout."""
    h, w = image_bgr.shape[:2]
    # Tuned from real user samples (blue target box).
    x1 = int(0.235 * w)
    x2 = int(0.748 * w)
    y1 = int(0.403 * h)
    y2 = int(0.887 * h)
    return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float32)


def _is_detection_unreliable(points: np.ndarray, image_bgr: np.ndarray) -> bool:
    """Heuristic gate to switch to template ROI when contour geometry is implausible."""
    rect = order_points(points)
    tl, tr, br, bl = rect
    h, w = image_bgr.shape[:2]

    x, y, bw, bh = cv2.boundingRect(rect.astype(np.int32))
    width_ratio = bw / max(1.0, float(w))
    x_ratio = x / max(1.0, float(w))
    top_tilt = abs(float(tr[1] - tl[1])) / max(1.0, float(bw))

    if width_ratio < 0.40 or width_ratio > 0.85:
        return True
    if x_ratio < 0.08 or x_ratio > 0.36:
        return True
    if top_tilt > 0.09:
        return True
    return False


def _snap_roi_to_dark_grid_lines(
    image_bgr: np.ndarray,
    points: np.ndarray,
    search_px: int = 18,
) -> np.ndarray:
    """
    Snap ROI edges to nearest strong dark grid lines to avoid off-by-one-column/row boxes.
    """
    rect = order_points(points)
    tl, tr, br, bl = rect

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    inv = cv2.bitwise_not(blur)  # dark lines become high values

    h, w = inv.shape[:2]

    x_left = int(round((tl[0] + bl[0]) / 2.0))
    x_right = int(round((tr[0] + br[0]) / 2.0))
    y_top = int(round((tl[1] + tr[1]) / 2.0))
    y_bottom = int(round((bl[1] + br[1]) / 2.0))

    x_left = max(0, min(w - 1, x_left))
    x_right = max(0, min(w - 1, x_right))
    y_top = max(0, min(h - 1, y_top))
    y_bottom = max(0, min(h - 1, y_bottom))

    if x_right <= x_left + 4 or y_bottom <= y_top + 4:
        return rect

    row_slice = slice(max(0, y_top), min(h, y_bottom + 1))
    col_slice = slice(max(0, x_left), min(w, x_right + 1))

    def _snap_x(x0: int) -> int:
        a = max(0, x0 - search_px)
        b = min(w - 1, x0 + search_px)
        if b <= a:
            return x0
        profile = inv[row_slice, a:b + 1].sum(axis=0)
        return int(a + int(profile.argmax()))

    def _snap_y(y0: int, prefer_up: bool) -> int:
        if prefer_up:
            a = max(0, y0 - search_px)
            b = min(h - 1, y0 + max(4, search_px // 3))
        else:
            a = max(0, y0 - max(4, search_px // 3))
            b = min(h - 1, y0 + search_px)
        if b <= a:
            return y0
        profile = inv[a:b + 1, col_slice].sum(axis=1)
        y = int(a + int(profile.argmax()))
        # Small upward nudge for top edge to avoid one-line-below clipping.
        if prefer_up:
            y = max(0, y - 2)
        return y

    x_left_s = _snap_x(x_left)
    x_right_s = _snap_x(x_right)
    y_top_s = _snap_y(y_top, prefer_up=True)
    y_bottom_s = _snap_y(y_bottom, prefer_up=False)

    if x_right_s <= x_left_s + 4 or y_bottom_s <= y_top_s + 4:
        return rect

    snapped = np.array(
        [
            [x_left_s, y_top_s],
            [x_right_s, y_top_s],
            [x_right_s, y_bottom_s],
            [x_left_s, y_bottom_s],
        ],
        dtype=np.float32,
    )
    return snapped


def _expand_right_edge_to_grid(
    image_bgr: np.ndarray,
    points: np.ndarray,
    search_right_px: int = 90,
) -> np.ndarray:
    """Expand ROI right edge to nearest strong vertical dark line on the right."""
    rect = order_points(points)
    tl, tr, br, bl = rect

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    inv = cv2.bitwise_not(blur)

    h, w = inv.shape[:2]
    x_left = int(round((tl[0] + bl[0]) / 2.0))
    x_right = int(round((tr[0] + br[0]) / 2.0))
    y_top = int(round((tl[1] + tr[1]) / 2.0))
    y_bottom = int(round((bl[1] + br[1]) / 2.0))

    x_left = max(0, min(w - 1, x_left))
    x_right = max(0, min(w - 1, x_right))
    y_top = max(0, min(h - 1, y_top))
    y_bottom = max(0, min(h - 1, y_bottom))

    if y_bottom <= y_top + 4:
        return rect

    a = max(0, x_right - 8)
    b = min(w - 1, x_right + max(20, search_right_px))
    if b <= a:
        return rect

    row_slice = slice(y_top, y_bottom + 1)
    profile = inv[row_slice, a:b + 1].sum(axis=0)
    new_right = int(a + int(profile.argmax()))

    # Never move inward too much; only keep or expand.
    new_right = max(x_right, new_right)
    if new_right <= x_left + 10:
        return rect

    expanded = np.array(
        [
            [x_left, y_top],
            [new_right, y_top],
            [new_right, y_bottom],
            [x_left, y_bottom],
        ],
        dtype=np.float32,
    )
    return expanded


def _maybe_trim_to_ab_grid(points: np.ndarray, right_ratio: float = 0.73) -> Tuple[np.ndarray, bool, float]:
    """
    If detected polygon is too wide (includes summary columns), trim right side to A/B grid area.
    Returns: (new_points, trimmed, original_aspect)
    """
    rect = order_points(points)
    tl, tr, br, bl = rect

    top_w = float(np.linalg.norm(tr - tl))
    bot_w = float(np.linalg.norm(br - bl))
    h_l = float(np.linalg.norm(bl - tl))
    h_r = float(np.linalg.norm(br - tr))

    avg_w = (top_w + bot_w) / 2.0
    avg_h = max(1.0, (h_l + h_r) / 2.0)
    aspect = avg_w / avg_h

    # Wide table likely includes right summary columns; trim to session block.
    if aspect <= 1.85:
        return rect, False, aspect

    alpha = max(0.55, min(0.85, right_ratio))
    new_tr = tl + alpha * (tr - tl)
    new_br = bl + alpha * (br - bl)

    trimmed = np.array([tl, new_tr, new_br, bl], dtype=np.float32)
    return trimmed, True, aspect


def warp_perspective(
    image_bgr: np.ndarray,
    points: np.ndarray,
    out_width: int = WARP_WIDTH,
    out_height: int = WARP_HEIGHT,
) -> np.ndarray:
    """Apply perspective transform to obtain a normalized top-down table image."""
    src = order_points(points)
    dst = np.array(
        [
            [0, 0],
            [out_width - 1, 0],
            [out_width - 1, out_height - 1],
            [0, out_height - 1],
        ],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(image_bgr, matrix, (out_width, out_height))
    return warped


def extract_cells(
    warped_bgr: np.ndarray,
    n_rows: int = N_ROWS,
    n_cols: int = N_COLS,
    save_debug_cells: bool = False,
) -> List[List[np.ndarray]]:
    """
    Divide normalized table into a fixed n_rows x n_cols grid and return cell images.
    """
    h, w = warped_bgr.shape[:2]
    cell_h = h / n_rows
    cell_w = w / n_cols

    cells: List[List[np.ndarray]] = []
    for r in range(n_rows):
        row_cells: List[np.ndarray] = []
        for c in range(n_cols):
            y1 = int(r * cell_h)
            x1 = int(c * cell_w)
            y2 = h if r == n_rows - 1 else int((r + 1) * cell_h)
            x2 = w if c == n_cols - 1 else int((c + 1) * cell_w)

            cell = warped_bgr[y1:y2, x1:x2]
            row_cells.append(cell)

            if save_debug_cells:
                debug_path = os.path.join(DEBUG_CELLS_DIR, f"row{r+1:02d}_col{c+1:02d}.png")
                cv2.imwrite(debug_path, cell)

        cells.append(row_cells)

    return cells


def _draw_detected_contour(image_bgr: np.ndarray, points: np.ndarray) -> np.ndarray:
    contour_vis = image_bgr.copy()
    pts_int = points.astype(np.int32).reshape((-1, 1, 2))
    cv2.polylines(contour_vis, [pts_int], True, (0, 255, 0), 3)
    return contour_vis


def _draw_grid_overlay(image_bgr: np.ndarray, n_rows: int, n_cols: int) -> np.ndarray:
    overlay = image_bgr.copy()
    h, w = overlay.shape[:2]

    for r in range(1, n_rows):
        y = int(r * h / n_rows)
        cv2.line(overlay, (0, y), (w - 1, y), (0, 255, 255), 1)

    for c in range(1, n_cols):
        x = int(c * w / n_cols)
        cv2.line(overlay, (x, 0), (x, h - 1), (0, 255, 255), 1)

    return overlay
def _encode_image_to_data_url(image_bgr: np.ndarray) -> str:
    """Encode OpenCV image as PNG data URL for frontend preview."""
    ok, encoded = cv2.imencode(".png", image_bgr)
    if not ok:
        raise ValueError("Failed to encode debug image")
    b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _preprocess_cell(cell_bgr: np.ndarray) -> torch.Tensor:
    """Convert BGR cell to normalized 1x28x28 tensor on correct device."""
    cell_rgb = cv2.cvtColor(cell_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(cell_rgb)
    tensor = _cell_transform(pil_img).unsqueeze(0).to(_device)
    return tensor


def _predict_cell_label(model, cell_bgr: np.ndarray) -> str:
    """Run model on one cell and return A or B."""
    with torch.no_grad():
        x = _preprocess_cell(cell_bgr)
        logit = model(x)
        prob_b = torch.sigmoid(logit)[0].item()
    return "B" if prob_b >= 0.6 else "A"


def predict_ab_table_from_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    End-to-end OCR extraction pipeline:
    - preprocess image
    - detect outer table contour (4 points)
    - perspective warp to fixed size
    - extract fixed 18 x 20 cell grid
    - classify each cell as A/B
    """
    try:
        image_bgr = _bytes_to_bgr(file_bytes)

        # Requested detection order:
        # 1) grid lines, 2) largest 4-point rectangle, 3) template ROI fallback.
        preprocessed = preprocess_image(image_bgr)
        detection_error = None
        trimmed_ab_grid = False
        detected_aspect = 0.0
        used_template_roi = False
        template_locked = False

        # Save intermediate edge map for debugging.
        cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, "latest_edges.png"), preprocessed)

        contour_candidates_vis = image_bgr.copy()
        contour_vis = image_bgr.copy()
        table_points = None
        detection_strategy = None

        # 1) Primary: detect using grid lines.
        try:
            _, grid_points, grid_mask = _detect_table_from_grid_lines(image_bgr)
            table_points = grid_points
            preprocessed = grid_mask
            detection_strategy = "grid_lines"
            contour_candidates_vis = cv2.cvtColor(grid_mask, cv2.COLOR_GRAY2BGR)
        except Exception as grid_err:
            detection_error = grid_err

        # 2) Fallback: largest valid 4-point rectangle from contours.
        if table_points is None:
            try:
                _, rect_points, contour_candidates_vis, contour_vis = detect_largest_rectangle(
                    preprocessed,
                    image_bgr,
                    min_area_ratio=0.02,
                )
                table_points = rect_points
                detection_strategy = "largest_4point_rectangle"
            except Exception as rect_err:
                detection_error = rect_err

        # 3) Final fallback: template ROI.
        if table_points is None:
            table_points = _template_roi_points(image_bgr)
            used_template_roi = True
            detection_strategy = "template_roi_fallback"

        # Stabilize output for this fixed form layout: lock to calibrated ROI.
        table_points = _template_roi_points(image_bgr)
        used_template_roi = True
        template_locked = True
        detection_strategy = (
            f"{detection_strategy}+template_lock"
            if detection_strategy
            else "template_lock"
        )

        # Optional trim if detected polygon is wider than A/B session block.
        if not template_locked:
            table_points, trimmed_ab_grid, detected_aspect = _maybe_trim_to_ab_grid(
                table_points,
                right_ratio=0.73,
            )

        # Snap/expand borders for exact grid alignment.
        if template_locked:
            # For locked template ROI, only expand right edge outward to include missing columns.
            table_points = _expand_right_edge_to_grid(image_bgr, table_points, search_right_px=100)
        else:
            table_points = _snap_roi_to_dark_grid_lines(image_bgr, table_points, search_px=18)

        # Safety gate to switch to template ROI only when geometry is implausible.
        if _is_detection_unreliable(table_points, image_bgr):
            table_points = _template_roi_points(image_bgr)
            used_template_roi = True
            detection_strategy = (
                f"{detection_strategy}+template_roi"
                if detection_strategy
                else "template_roi"
            )

        contour_vis = _draw_detected_contour(image_bgr, table_points)

        # Bonus: save contour stages.
        cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, "latest_all_contours.png"), contour_candidates_vis)
        cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, "latest_detected_contour.png"), contour_vis)

        warped_table = warp_perspective(
            image_bgr,
            table_points,
            out_width=WARP_WIDTH,
            out_height=WARP_HEIGHT,
        )

        grid_cells = extract_cells(
            warped_table,
            n_rows=N_ROWS,
            n_cols=N_COLS,
            save_debug_cells=True,
        )

        # Debug outputs: warped image, grid overlay, and preprocessing stage.
        grid_overlay = _draw_grid_overlay(warped_table, N_ROWS, N_COLS)
        cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, "latest_warped_table.png"), warped_table)
        cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, "latest_grid_overlay.png"), grid_overlay)
        cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, "latest_preprocessed.png"), preprocessed)

        model = _get_model()

        extracted_data: Dict[str, List[str]] = {}
        table_rows: List[Dict[str, Any]] = []
        total_A = 0
        total_B = 0

        for row_idx, skill in enumerate(SKILL_AREAS):
            session_values: List[str] = []
            for col_idx in range(N_COLS):
                cell_img = grid_cells[row_idx][col_idx]
                label = _predict_cell_label(model, cell_img)
                session_values.append(label)
                if label == "A":
                    total_A += 1
                else:
                    total_B += 1

            extracted_data[skill] = session_values

            row_total_a = session_values.count("A")
            row_total_b = session_values.count("B")

            row: Dict[str, Any] = {
                "Student Name": "",
                "Register Number": "",
                "Skill Area": skill,
                "Total A": str(row_total_a),
                "Total B": str(row_total_b),
                "I Qr": "",
                "II Qr": "",
                "III Qr": "",
                "IV Qr": "",
                "Assessment Date": "",
            }
            for i, value in enumerate(session_values, start=1):
                row[f"Session {i}"] = value

            table_rows.append(row)

        extraction_report = [f"{skill}: [{', '.join(vals)}]" for skill, vals in extracted_data.items()]

        table_dict = {
            "headers": HEADERS,
            "rows": table_rows,
            "row_count": len(table_rows),
            "extracted_values": extracted_data,
            "extraction_report": extraction_report,
        }

        extraction_summary = {
            "total_cells": N_ROWS * N_COLS,
            "total_A": total_A,
            "total_B": total_B,
            "skills_found": list(extracted_data.keys()),
            "normalized_size": {"width": WARP_WIDTH, "height": WARP_HEIGHT},
            "grid_shape": {"rows": N_ROWS, "cols": N_COLS},
            "cell_count": N_ROWS * N_COLS,
        }

        return {
            "success": True,
            "method": "cnn_perspective_grid_ocr",
            "tables": [table_dict],
            "table_count": 1,
            "extracted_data": extracted_data,
            "table_detection": {
                "detected": True,
                "points": table_points.astype(int).tolist(),
                "warped": True,
                "strategy": detection_strategy,
                "trimmed_ab_grid": trimmed_ab_grid,
                "detected_aspect": round(float(detected_aspect), 3),
                "used_template_roi": used_template_roi,
                "debug_visualization": {
                    "detected_contour": _encode_image_to_data_url(contour_vis),
                    "warped_table": _encode_image_to_data_url(warped_table),
                    "grid_overlay": _encode_image_to_data_url(grid_overlay),
                },
            },
            "extraction_summary": extraction_summary,
        }

    except Exception as e:
        print("CNN-based OCR error:", e)
        return {
            "success": False,
            "error": str(e),
            "tables": [],
            "table_count": 0,
        }













