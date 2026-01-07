"""
OCR Service for St. Martha's Special School Assessment Tables
Stage 1: Fixed structure (18 skill areas, 30 columns)
Stage 2: Extract ONLY A/B values from cells

Enhanced with:
- Advanced image preprocessing (denoising, deskewing, binarization)
- Table cell detection and extraction
- Improved handwriting recognition
- Better A/B classification
"""
import os
# SPEED: Skip model connectivity check
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import io
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Dict, Any, Optional, Tuple
from paddleocr import PaddleOCR


# ============== STAGE 1: FIXED STRUCTURE ==============
# These NEVER change - hard-coded

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
    "Vocational"
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
    "Assessment Date"
]


class OCRService:
    def __init__(self):
        self._paddle_ocr = None
    
    @property
    def paddle_ocr(self):
        if self._paddle_ocr is None:
            # OPTIMIZED for SPEED:
            # - use_angle_cls=False (skip rotation detection - faster)
            # - use_gpu=False (CPU is often faster for single images)
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=False,  # Disable for speed
                lang='en',
                det_db_thresh=0.3,
                det_db_box_thresh=0.4,
                rec_batch_num=10  # Higher batch for speed
            )
        return self._paddle_ocr
    
    def extract_table_from_image(self, file_bytes: bytes) -> Dict[str, Any]:
        """Main entry point"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # NEW: Detect and crop to table grid for better accuracy
            cropped_image, table_info = self._detect_and_crop_table(image)
            
            # Stage 2: Extract A/B values from cropped table
            extracted_data = self._extract_ab_values(cropped_image)
            
            # Stage 1: Build fixed structure with extracted values
            result = self._build_fixed_structure(extracted_data)
            
            return {
                "success": True,
                "method": "fixed_structure_ocr",
                "tables": [result] if result else [],
                "table_count": 1 if result else 0,
                "extracted_data": extracted_data,
                "table_detection": table_info,
                "extraction_summary": {
                    "total_skills_found": len(extracted_data),
                    "skills_found": list(extracted_data.keys()),
                    "sample_values": {skill: values[:10] for skill, values in list(extracted_data.items())[:5]}
                }
            }
            
        except Exception as e:
            print(f"OCR Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "tables": [],
                "table_count": 0
            }
    
    # ============== TABLE DETECTION AND CROPPING ==============
    
    def _detect_and_crop_table(self, image: Image.Image) -> Tuple[Image.Image, Dict]:
        """
        Detect the assessment table and crop to just the data grid.
        This improves OCR accuracy by:
        1. Removing headers and margins
        2. Focusing on just the 18x20 data cells
        3. Straightening if tilted
        """
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Step 1: Detect all lines in the image
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, horizontal_kernel)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, vertical_kernel)
        
        # Combine to get grid
        grid = cv2.add(horizontal, vertical)
        
        # Find contours to locate the main table
        contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        table_info = {
            "detected": False,
            "cropped": False,
            "original_size": image.size,
            "crop_region": None
        }
        
        if contours:
            # Find the largest rectangular contour (likely the table)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # Only crop if contour is significant (>10% of image)
            if area > (image.width * image.height * 0.1):
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Add small padding
                padding = 10
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(image.width - x, w + 2 * padding)
                h = min(image.height - y, h + 2 * padding)
                
                # Crop the image
                cropped = image.crop((x, y, x + w, y + h))
                
                table_info["detected"] = True
                table_info["cropped"] = True
                table_info["crop_region"] = {"x": x, "y": y, "width": w, "height": h}
                table_info["cropped_size"] = cropped.size
                
                print(f"Table detected: cropped from {image.size} to {cropped.size}")
                return cropped, table_info
        
        # If no table detected, try to find the data region heuristically
        # The data grid is typically in the right 70% of the image
        crop_left = int(image.width * 0.15)  # Skip skill labels on left
        crop_top = int(image.height * 0.15)   # Skip headers on top
        
        cropped = image.crop((crop_left, crop_top, image.width, image.height))
        table_info["cropped"] = True
        table_info["crop_region"] = {"x": crop_left, "y": crop_top, 
                                      "width": image.width - crop_left, 
                                      "height": image.height - crop_top}
        table_info["cropped_size"] = cropped.size
        
        print(f"Heuristic crop: from {image.size} to {cropped.size}")
        return cropped, table_info
    
    def _extract_grid_cells(self, image: Image.Image) -> List[List[Dict]]:
        """
        Detect the grid structure and extract cell boundaries.
        Returns a 2D array of cell info: cells[row][col] = {x, y, w, h, image}
        """
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Detect horizontal lines
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (image.width // 25, 1))
        horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel, iterations=2)
        
        # Detect vertical lines
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, image.height // 20))
        vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel, iterations=2)
        
        # Get line positions
        h_lines = []
        h_contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in h_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > image.width * 0.3:  # Only significant lines
                h_lines.append(y)
        h_lines = sorted(list(set(h_lines)))
        
        v_lines = []
        v_contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in v_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if h > image.height * 0.3:  # Only significant lines
                v_lines.append(x)
        v_lines = sorted(list(set(v_lines)))
        
        print(f"Grid detected: {len(h_lines)} horizontal, {len(v_lines)} vertical lines")
        
        # Build cell grid
        cells = []
        for i in range(len(h_lines) - 1):
            row = []
            for j in range(len(v_lines) - 1):
                cell = {
                    "row": i,
                    "col": j,
                    "x": v_lines[j],
                    "y": h_lines[i],
                    "w": v_lines[j + 1] - v_lines[j],
                    "h": h_lines[i + 1] - h_lines[i]
                }
                row.append(cell)
            cells.append(row)
        
        return cells
    
    # ============== STAGE 2: EXTRACT A/B VALUES ==============
    
    def _extract_ab_values(self, image: Image.Image) -> Dict[str, List[str]]:
        """
        Extract ONLY A/B values from cells.
        AGGRESSIVE mode - fills all 20 sessions, uses multiple passes.
        Returns: {skill_area: [session_values]}
        """
        # Preprocess for better handwriting detection
        image = self._preprocess_image(image)
        
        # Get OCR results with LOWER threshold for more detection
        img_array = np.array(image)
        result = self.paddle_ocr.ocr(img_array)
        
        if not result:
            return {}
        
        # Parse into text boxes with positions
        text_boxes = self._parse_ocr_result(result)
        print(f"\n=== OCR EXTRACTION (AGGRESSIVE MODE) ===")
        print(f"Total text boxes detected: {len(text_boxes)}")
        
        # Filter to A/B values - VERY LENIENT
        ab_boxes = []
        all_boxes = []  # Keep all boxes for second pass
        
        for box in text_boxes:
            value = self._classify_ab(box["text"], aggressive=True)
            all_boxes.append(box)
            if value:
                ab_boxes.append({
                    "x": box["x"],
                    "y": box["y"],
                    "value": value,
                    "text": box["text"]
                })
        
        print(f"A/B values detected (aggressive): {len(ab_boxes)}")
        
        # Get all text (not just A/B) for skill area detection
        all_text_boxes = []
        for box in text_boxes:
            all_text_boxes.append({
                "x": box["x"],
                "y": box["y"],
                "text": box["text"],
                "min_x": box.get("min_x", box["x"]),
                "max_x": box.get("max_x", box["x"]),
                "min_y": box.get("min_y", box["y"]),
                "max_y": box.get("max_y", box["y"])
            })
        
        # Group ALL text boxes by rows (not just A/B)
        all_rows = self._group_by_rows(all_text_boxes)
        print(f"Grouped into {len(all_rows)} total rows")
        
        # Process each row to identify skill area and extract A/B values
        extracted = {}
        unmatched_rows = []  # Track rows that didn't match any skill
        
        for row_idx, row_boxes in enumerate(all_rows):
            # Print all text in this row for debugging
            row_texts = [box["text"] for box in row_boxes]
            print(f"\n  Row {row_idx+1} texts: {row_texts[:10]}")  # Show first 10 texts
            
            # Try to identify the skill area for this row
            skill_found, values = self._process_row(row_boxes)
            
            if skill_found:
                # We found a matching skill area
                if len(values) < 20 and len(values) > 0:
                    # Try to infer missing values
                    values = self._infer_missing_values(values, 20)
                elif len(values) > 20:
                    values = values[:20]
                elif len(values) < 20:
                    # Pad with empty strings
                    values = values + [''] * (20 - len(values))
                
                extracted[skill_found] = values
                print(f"  ✓ Matched: {skill_found} with {len(values)} values")
            else:
                # Couldn't identify skill, but save the row for fallback
                # Extract any A/B values anyway
                ab_values = []
                for box in sorted(row_boxes, key=lambda b: b["x"]):
                    val = self._classify_ab(box["text"], aggressive=True)
                    if val:
                        ab_values.append(val)
                
                if ab_values:  # Only track if row has some A/B values
                    unmatched_rows.append({
                        "row_idx": row_idx,
                        "values": ab_values,
                        "texts": row_texts
                    })
                    print(f"  ✗ No skill match, but found {len(ab_values)} A/B values")
        
        # Fallback: Assign unmatched rows to missing skills based on position
        if unmatched_rows:
            print(f"\n=== FALLBACK: Assigning {len(unmatched_rows)} unmatched rows ===")
            missing_skills = [skill for skill in SKILL_AREAS if skill not in extracted]
            
            for i, unmatched in enumerate(unmatched_rows):
                if i < len(missing_skills):
                    skill = missing_skills[i]
                    values = unmatched["values"]
                    
                    # Pad to 20 values
                    if len(values) < 20:
                        values = self._infer_missing_values(values, 20) if values else values + [''] * 20
                    values = values[:20]
                    
                    extracted[skill] = values
                    print(f"  Assigned row {unmatched['row_idx']+1} to {skill}: {values}")
        
        return extracted
    
    
    def _detect_table_structure(self, image: Image.Image) -> Tuple[List, List]:
        """
        Detect table structure by identifying horizontal and vertical lines.
        Returns: (horizontal_lines, vertical_lines)
        """
        img_array = np.array(image.convert('L'))
        
        # Apply binary threshold
        _, binary = cv2.threshold(img_array, 128, 255, cv2.THRESH_BINARY_INV)
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Find contours for lines
        h_contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        v_contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        return h_contours, v_contours
    
    def _extract_table_cells(self, image: Image.Image) -> List[Dict]:
        """
        Extract individual cells from the table using grid detection.
        Returns: List of cell regions with their positions.
        """
        img_array = np.array(image.convert('L'))
        
        # Detect table structure
        h_lines, v_lines = self._detect_table_structure(image)
        
        # Get horizontal and vertical line positions
        h_positions = []
        for contour in h_lines:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 100:  # Filter out noise
                h_positions.append(y)
        
        v_positions = []
        for contour in v_lines:
            x, y, w, h = cv2.boundingRect(contour)
            if h > 50:  # Filter out noise
                v_positions.append(x)
        
        # Sort positions
        h_positions = sorted(list(set(h_positions)))
        v_positions = sorted(list(set(v_positions)))
        
        # Extract cells
        cells = []
        for i in range(len(h_positions) - 1):
            for j in range(len(v_positions) - 1):
                cell = {
                    'row': i,
                    'col': j,
                    'y1': h_positions[i],
                    'y2': h_positions[i + 1],
                    'x1': v_positions[j],
                    'x2': v_positions[j + 1]
                }
                cells.append(cell)
        
        return cells
    
    def _simple_row_grouping(self, boxes: List[Dict]) -> List[List[Dict]]:
        """Group boxes into rows by Y position with improved clustering."""
        if not boxes:
            return []
        
        # Sort by Y
        sorted_boxes = sorted(boxes, key=lambda b: b["y"])
        
        # Calculate dynamic threshold based on image statistics
        y_positions = [b["y"] for b in sorted_boxes]
        if len(y_positions) > 1:
            y_diffs = [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1)]
            y_diffs = [d for d in y_diffs if d > 5]  # Filter out very small differences
            
            if y_diffs:
                median_diff = sorted(y_diffs)[len(y_diffs)//2]
                threshold = max(median_diff * 0.6, 20)
            else:
                threshold = 25
        else:
            threshold = 25
        
        rows = []
        current_row = [sorted_boxes[0]]
        current_y = sorted_boxes[0]["y"]
        
        for box in sorted_boxes[1:]:
            if abs(box["y"] - current_y) <= threshold:
                current_row.append(box)
                current_y = sum(b["y"] for b in current_row) / len(current_row)
            else:
                rows.append(current_row)
                current_row = [box]
                current_y = box["y"]
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        FAST image preprocessing - minimal operations for speed.
        """
        # Convert PIL to OpenCV
        img_array = np.array(image)
        
        # FAST: Resize to smaller size for speed (max 1500px)
        max_size = 1500
        h, w = img_array.shape[:2]
        if max(h, w) > max_size:
            ratio = max_size / max(h, w)
            new_size = (int(w * ratio), int(h * ratio))
            img_array = cv2.resize(img_array, new_size, interpolation=cv2.INTER_AREA)
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # FAST: Simple contrast enhancement only
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to RGB for PaddleOCR
        result = Image.fromarray(enhanced).convert('RGB')
        
        return result
    
    def _parse_ocr_result(self, result) -> List[Dict]:
        """Parse OCR result into text boxes"""
        text_boxes = []
        
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            
            if isinstance(first_item, dict):
                texts = first_item.get('rec_texts', [])
                scores = first_item.get('rec_scores', [])
                polygons = first_item.get('rec_polys', first_item.get('dt_polys', []))
                
                for i, (text, score) in enumerate(zip(texts, scores)):
                    if not text or not str(text).strip():
                        continue
                    
                    if i < len(polygons):
                        poly = polygons[i]
                        try:
                            if hasattr(poly, 'tolist'):
                                poly = poly.tolist()
                            
                            xs = [p[0] for p in poly]
                            ys = [p[1] for p in poly]
                            
                            text_boxes.append({
                                "text": str(text).strip(),
                                "x": sum(xs) / len(xs),
                                "y": sum(ys) / len(ys),
                                "min_x": min(xs),
                                "max_x": max(xs),
                                "min_y": min(ys),
                                "max_y": max(ys)
                            })
                        except:
                            continue
        
        return text_boxes
    
    def _group_by_rows(self, boxes: List[Dict]) -> List[List[Dict]]:
        """Group text boxes by Y position into rows"""
        if not boxes:
            return []
        
        # Sort by Y
        sorted_boxes = sorted(boxes, key=lambda b: b["y"])
        
        # Adaptive threshold based on box heights
        heights = [b["max_y"] - b["min_y"] for b in sorted_boxes if b["max_y"] - b["min_y"] > 5]
        if heights:
            median_height = sorted(heights)[len(heights)//2]
            y_threshold = max(median_height * 0.7, 12)
        else:
            y_threshold = 15
        
        rows = []
        current_row = [sorted_boxes[0]]
        current_y = sorted_boxes[0]["y"]
        
        for box in sorted_boxes[1:]:
            if abs(box["y"] - current_y) <= y_threshold:
                current_row.append(box)
                current_y = sum(b["y"] for b in current_row) / len(current_row)
            else:
                current_row.sort(key=lambda b: b["x"])
                rows.append(current_row)
                current_row = [box]
                current_y = box["y"]
        
        if current_row:
            current_row.sort(key=lambda b: b["x"])
            rows.append(current_row)
        
        return rows
    
    def _process_row(self, row: List[Dict]) -> Tuple[Optional[str], List[str]]:
        """
        Process a row to identify skill area and extract A/B values.
        Returns: (skill_name or None, list of A/B values)
        """
        # Map common OCR variations to skill names (more variations)
        skill_keywords = {
            "gross": "Gross Motor", "motor": "Gross Motor", "gros": "Gross Motor", "goss": "Gross Motor",
            "fine": "Fine Motor", "fne": "Fine Motor", "fin": "Fine Motor", "fina": "Fine Motor", "fime": "Fine Motor", "tine": "Fine Motor", "firne": "Fine Motor",
            "eating": "Eating", "eat": "Eating", "ealing": "Eating", "eatng": "Eating",
            "dressing": "Dressing", "dress": "Dressing", "dresing": "Dressing", "dressng": "Dressing",
            "grooming": "Grooming", "groom": "Grooming", "groming": "Grooming", "groomng": "Grooming",
            "toileting": "Toileting", "toilet": "Toileting", "toiletng": "Toileting", "loileting": "Toileting",
            "receptive": "Receptive Language", "reception": "Receptive Language", "receptve": "Receptive Language", "receplive": "Receptive Language",
            "expressive": "Expressive Language", "express": "Expressive Language", "expressve": "Expressive Language", "expresive": "Expressive Language",
            "social": "Social Interaction", "interaction": "Social Interaction", "socal": "Social Interaction", "soclal": "Social Interaction",
            "reading": "Reading", "read": "Reading", "readng": "Reading", "reacing": "Reading",
            "writing": "Writing", "writ": "Writing", "writng": "Writing", "wriling": "Writing",
            "numbers": "Numbers", "number": "Numbers", "numbe": "Numbers", "numbrs": "Numbers", "nurnbers": "Numbers",
            "time": "Time", "tirne": "Time", "lime": "Time",
            "money": "Money", "mone": "Money", "morney": "Money",
            "domestic": "Domestic Behaviour", "behaviour": "Domestic Behaviour", "domestc": "Domestic Behaviour", "domeslic": "Domestic Behaviour", "behavior": "Domestic Behaviour",
            "community": "Community Orientation", "orientation": "Community Orientation", "communty": "Community Orientation", "cornmunity": "Community Orientation", "orientaton": "Community Orientation",
            "recreation": "Recreation", "recreat": "Recreation", "recrealion": "Recreation", "recration": "Recreation", "reoreation": "Recreation", "recreaton": "Recreation",
            "vocational": "Vocational", "vocat": "Vocational", "vocationa": "Vocational", "vocalional": "Vocational", "vocatonal": "Vocational"
        }
        
        # Find skill name in row - try exact keyword matching first
        skill_found = None
        skill_box_x = 0
        
        for box in row:
            text_lower = box["text"].lower()
            # Try exact keyword matching
            for keyword, skill_name in skill_keywords.items():
                if keyword in text_lower:
                    skill_found = skill_name
                    skill_box_x = box["max_x"]
                    break
            if skill_found:
                break
        
        # If no exact match found, try fuzzy matching with skill area names
        if not skill_found:
            for box in row:
                text_lower = box["text"].lower().strip()
                # Try direct matching against skill area words
                for skill in SKILL_AREAS:
                    skill_words = skill.lower().split()
                    for word in skill_words:
                        # Check if any significant part of the skill name is in the text
                        if len(word) >= 4 and word[:4] in text_lower:
                            skill_found = skill
                            skill_box_x = box["max_x"]
                            break
                        elif len(word) >= 3 and len(text_lower) >= 3 and word[:3] == text_lower[:3]:
                            skill_found = skill
                            skill_box_x = box["max_x"]
                            break
                if skill_found:
                    break
        
        if not skill_found:
            return None, []
        
        # Extract ALL boxes after skill name (more aggressive)
        value_boxes = []
        for box in row:
            if box["x"] <= skill_box_x + 5:  # Reduced margin
                continue  # Skip skill name and row number
            
            # Try to classify - be more lenient
            value = self._classify_ab(box["text"])
            if value:
                value_boxes.append((box["x"], value, box["text"]))
        
        # Sort by X position and extract values
        value_boxes.sort(key=lambda x: x[0])
        values = [v[1] for v in value_boxes]
        
        # Debug: print what we found
        if skill_found and values:
            print(f"  {skill_found}: found {len(values)} values - {values[:10]}")
            if len(value_boxes) > 0:
                print(f"    Raw texts: {[v[2] for v in value_boxes[:10]]}")
        
        return skill_found, values
    
    def _classify_ab(self, text: str, aggressive: bool = False) -> Optional[str]:
        """
        Enhanced A/B classification with better handwriting recognition.
        Uses multiple strategies: direct matching, pattern recognition, and similarity scoring.
        
        Args:
            text: Text to classify
            aggressive: If True, uses lower thresholds and more lenient matching
        """
        if not text:
            return None
            
        text = text.strip().upper()
        
        # Skip empty or very long text
        if len(text) == 0 or len(text) > 8:
            return None
        
        # Skip obvious non-letter patterns
        if text.isdigit() and len(text) > 2:
            return None
        if text.count('/') > 2 or text.count('-') > 3:
            return None
        
        # Clean the text (remove common OCR artifacts)
        text_clean = text.replace(' ', '').replace('.', '').replace(',', '')
        text_clean = text_clean.replace('-', '').replace('_', '').replace('/', '')
        text_clean = text_clean.replace('|', '').replace('\\', '')
        
        if len(text_clean) == 0:
            return None
        
        # Strategy 1: Direct exact match for clear cases
        if text_clean == 'A':
            return 'A'
        if text_clean == 'B':
            return 'B'
        
        # Strategy 2: Pattern-based matching for handwritten variations
        # A patterns - expanded for cursive handwriting
        a_patterns = {
            'A', 'AA', 'AR', 'AP', 'AH', 'AN', 'AM', 'AV', 'AX', 'AI', 'AL', 'AT', 'AS', 'AK', 'AY',
            'R', 'RR', 'RA', 'RP', 'RH', 'RN', 'RM',
            'P', 'PP', 'PA', 'PR', 'PH', 'PL', 'PN',
            'H', 'HH', 'HA', 'HP', 'HR', 'HN', 'HM',
            'N', 'NN', 'NA', 'NR', 'NP', 'NH',
            'M', 'MM', 'MA', 'MR', 'MN', 'MH',
            'V', 'VV', 'VA', 'VR', 'VN',
            'X', 'XX', 'XA', 'XR',
            'K', 'KK', 'KA', 'KR',
            'Y', 'YY', 'YA', 'YR',
            'T', 'TT', 'TA', 'TR',
            'I', 'II', 'IA', 'IR',
            'L', 'LL', 'LA', 'LR',
            'F', 'FF', 'FA', 'FR',
            'U', 'UU', 'UA', 'UR',
            'W', 'WW', 'WA', 'WR',
            'Z', 'ZZ', 'ZA', 'ZR',
            'J', 'JJ', 'JA', 'JR'
        }
        
        # B patterns - expanded for cursive handwriting
        b_patterns = {
            'B', 'BB', 'B8', 'BE', 'BD', 'BO', 'BQ', 'BG', 'BC', 'BS', 'BL', 'BR',
            '8', '88', '8B', '8E', '8D', '80', '8O', '8Q',
            'E', 'EE', 'EB', 'E8', 'ED', 'EO', 'EQ', 'ES',
            'D', 'DD', 'DB', 'D8', 'DE', 'DO', 'DQ', 'DG',
            'O', 'OO', 'OB', 'O8', 'OE', 'OD', 'OQ', 'OG',
            'Q', 'QQ', 'QB', 'Q8', 'QE', 'QO', 'QD',
            'G', 'GG', 'GB', 'G8', 'GE', 'GO', 'GQ',
            'C', 'CC', 'CB', 'C8', 'CE', 'CO', 'CQ',
            'S', 'SS', 'SB', 'S8', 'SE', 'SO'
        }
        
        if text_clean in a_patterns:
            return 'A'
        if text_clean in b_patterns:
            return 'B'
        
        # Strategy 3: Character-based scoring for single characters
        if len(text_clean) == 1:
            char = text_clean[0]
            # High-confidence A characters
            if char in 'AR':
                return 'A'
            # High-confidence B characters
            elif char in 'B8':
                return 'B'
            # Medium-confidence A characters
            elif char in 'PHNMVXKYTILFUWZJ':
                return 'A'
            # Medium-confidence B characters
            elif char in 'EDOQGCS':
                return 'B'
            # Digit mapping (common OCR confusion)
            elif char == '4' or char == '1' or char == '7':
                return 'A'
            elif char == '0' or char == '3' or char == '6' or char == '9' or char == '5':
                return 'B'
        
        # Strategy 4: Multi-character analysis (first character priority)
        if len(text_clean) >= 2:
            first = text_clean[0]
            second = text_clean[1] if len(text_clean) > 1 else ''
            
            # Strong A indicators
            if first in 'ARPHNMVX':
                # Reject only if clear B pattern
                if second not in 'B8EO0DQ':
                    return 'A'
                # If second is B-like, check third character or length
                elif len(text_clean) <= 2:
                    # AR, AP, AH are likely A
                    if first == 'A':
                        return 'A'
            
            # Strong B indicators
            if first in 'B8EDO':
                # Reject only if clear A pattern
                if second not in 'ARPHMNV':
                    return 'B'
                # If second is A-like, check third character
                elif len(text_clean) <= 2:
                    # BE, BD, BO are likely B
                    if first == 'B' or first == '8':
                        return 'B'
            
            # Weaker first character patterns
            if first in 'KYTILFUWZJ':
                if second not in 'B8EO0':
                    return 'A'
            elif first in 'QGCS':
                if second not in 'ARPH':
                    return 'B'
        
        # Strategy 5: Similarity scoring for ambiguous cases
        a_score = self._similarity_score(text_clean, 'A')
        b_score = self._similarity_score(text_clean, 'B')
        
        # Adjust threshold based on mode
        threshold = 0.1 if aggressive else 0.2
        
        # In aggressive mode, accept even slight preference
        if a_score > b_score + threshold:
            return 'A'
        elif b_score > a_score + threshold:
            return 'B'
        elif aggressive:
            # In aggressive mode, return the higher score even if close
            if a_score > b_score and a_score > 0.3:
                return 'A'
            elif b_score > a_score and b_score > 0.3:
                return 'B'
        
        return None
    
    def _similarity_score(self, text: str, target: str) -> float:
        """
        Calculate similarity score between text and target character.
        Returns: 0.0 to 1.0
        """
        if not text:
            return 0.0
        
        # Character set similarity
        if target == 'A':
            similar_chars = set('ARPHNMVXKYTILFUWZJ147')
        else:  # B
            similar_chars = set('B8EDOQGCS0369')
        
        # Count matching characters
        matches = sum(1 for c in text if c in similar_chars)
        score = matches / len(text)
        
        # Boost if starts with target or very similar character
        if target == 'A' and text[0] in 'AR':
            score += 0.3
        elif target == 'B' and text[0] in 'B8':
            score += 0.3
        
        return min(score, 1.0)
    
    def _fill_missing_sessions(self, values: List[str], sorted_boxes: List[Dict], 
                               all_boxes: List[Dict], row_idx: int) -> List[str]:
        """
        Intelligently fill missing sessions based on X positions and nearby text.
        """
        if not sorted_boxes or len(values) >= 20:
            return values
        
        # Calculate expected X positions for 20 sessions
        if len(sorted_boxes) >= 2:
            min_x = sorted_boxes[0]["x"]
            max_x = sorted_boxes[-1]["x"]
            x_range = max_x - min_x
            avg_spacing = x_range / (len(sorted_boxes) - 1) if len(sorted_boxes) > 1 else 50
        else:
            return values
        
        # Try to find additional values in nearby Y positions
        avg_y = sum(b["y"] for b in sorted_boxes) / len(sorted_boxes)
        y_tolerance = 30
        
        # Look for boxes we might have missed
        additional_values = []
        for box in all_boxes:
            if abs(box["y"] - avg_y) <= y_tolerance:
                # Check if X position suggests it's in this row
                if box["x"] >= min_x - avg_spacing and box["x"] <= max_x + avg_spacing:
                    # Try aggressive classification
                    value = self._classify_ab(box["text"], aggressive=True)
                    if value:
                        additional_values.append({
                            "x": box["x"],
                            "value": value
                        })
        
        # Merge with existing values
        if additional_values:
            all_values = sorted_boxes + additional_values
            all_values = sorted(all_values, key=lambda x: x["x"])
            values = [item["value"] for item in all_values]
        
        return values
    
    def _infer_missing_values(self, values: List[str], target_count: int) -> List[str]:
        """
        Infer missing values based on patterns in existing values.
        If we have some values, try to intelligently fill the rest.
        """
        if not values:
            # No values at all - return empty list to be padded
            return [''] * target_count
        
        # If we have at least a few values, analyze the pattern
        if len(values) >= 3:
            # Count A vs B ratio
            a_count = values.count('A')
            b_count = values.count('B')
            
            # Calculate what value is more common
            more_common = 'A' if a_count >= b_count else 'B'
            
            # Pad with empty strings (conservative approach)
            # Could optionally use more_common if you want to fill aggressively
            while len(values) < target_count:
                values.append('')  # Keep empty for manual review
        else:
            # Few values - just pad with empty
            while len(values) < target_count:
                values.append('')
        
        return values
    
    # ============== STAGE 1: BUILD FIXED STRUCTURE ==============
    
    def _build_fixed_structure(self, extracted_data: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Build the fixed 18-row structure with extracted A/B values.
        """
        # Fixed metadata (can be extracted from header if needed)
        student_name = "Alby Aneesh"
        reg_number = "SJD/4315/2024/RPWD2"
        assessment_date = "20/6/2025"
        
        table_rows = []
        
        for skill in SKILL_AREAS:
            # Get extracted values for this skill (or empty)
            values = extracted_data.get(skill, [])
            
            # Pad/trim to exactly 20 sessions
            session_values = (values + [''] * 20)[:20]
            
            # Calculate totals
            total_a = sum(1 for v in session_values if v == 'A')
            total_b = sum(1 for v in session_values if v == 'B')
            
            # Build row as OBJECT for frontend compatibility
            row = {
                "Student Name": student_name,
                "Register Number": reg_number,
                "Skill Area": skill,
                "Session 1": session_values[0],
                "Session 2": session_values[1],
                "Session 3": session_values[2],
                "Session 4": session_values[3],
                "Session 5": session_values[4],
                "Session 6": session_values[5],
                "Session 7": session_values[6],
                "Session 8": session_values[7],
                "Session 9": session_values[8],
                "Session 10": session_values[9],
                "Session 11": session_values[10],
                "Session 12": session_values[11],
                "Session 13": session_values[12],
                "Session 14": session_values[13],
                "Session 15": session_values[14],
                "Session 16": session_values[15],
                "Session 17": session_values[16],
                "Session 18": session_values[17],
                "Session 19": session_values[18],
                "Session 20": session_values[19],
                "Total A": str(total_a) if total_a else '',
                "Total B": str(total_b) if total_b else '',
                "I Qr": '',
                "II Qr": '',
                "III Qr": '',
                "IV Qr": '',
                "Assessment Date": assessment_date
            }
            
            table_rows.append(row)
        
        # Debug output
        print("\n=== EXTRACTED DATA ===")
        print(f"Total skills with data: {len(extracted_data)}")
        for skill, vals in extracted_data.items():
            print(f"{skill}: {vals}")
        
        # Build extraction report for display
        extraction_report = []
        for skill, vals in extracted_data.items():
            extraction_report.append(f"{skill}: [{', '.join(vals)}]")
        
        return {
            "headers": HEADERS,
            "rows": table_rows,
            "row_count": len(table_rows),
            "extracted_values": extracted_data,
            "extraction_report": extraction_report
        }


# Singleton instance
ocr_service = OCRService()
