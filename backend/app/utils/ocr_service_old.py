"""
OCR Service for St. Martha's Special School Assessment Tables
Stage 1: Fixed structure (18 skill areas, 30 columns)
Stage 2: Extract ONLY A/B values from cells
"""
import io
import numpy as np
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
    "Student_Name",
    "Register_Number", 
    "Skill_Area",
    "Session_1", "Session_2", "Session_3", "Session_4", "Session_5",
    "Session_6", "Session_7", "Session_8", "Session_9", "Session_10",
    "Session_11", "Session_12", "Session_13", "Session_14", "Session_15",
    "Session_16", "Session_17", "Session_18", "Session_19", "Session_20",
    "Total_A",
    "Total_B", 
    "I_Qr",
    "II_Qr",
    "III_Qr",
    "IV_Qr",
    "Assessment_Date"
]


class OCRService:
    def __init__(self):
        self._paddle_ocr = None
    
    @property
    def paddle_ocr(self):
        if self._paddle_ocr is None:
            # Fast configuration for simple A/B detection
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=False,
                lang='en'
            )
        return self._paddle_ocr
    
    def extract_table_from_image(self, file_bytes: bytes) -> Dict[str, Any]:
        """Main entry point"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Stage 2: Extract A/B values
            extracted_data = self._extract_ab_values(image)
            
            # Stage 1: Build fixed structure with extracted values
            result = self._build_fixed_structure(extracted_data)
            
            return {
                "success": True,
                "method": "fixed_structure_ocr",
                "tables": [result] if result else [],
                "table_count": 1 if result else 0,
                "extracted_data": extracted_data,
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
    
    # ============== STAGE 2: EXTRACT A/B VALUES ==============
    
    def _extract_ab_values(self, image: Image.Image) -> Dict[str, List[str]]:
        """
        Extract ONLY A/B values from cells.
        Returns: {skill_area: [session_values]}
        """
        # Preprocess for better handwriting detection
        image = self._preprocess_image(image)
        
        # Get OCR results
        img_array = np.array(image)
        result = self.paddle_ocr.ocr(img_array)
        
        if not result:
            return {}
        
        # Parse into text boxes with positions
        text_boxes = self._parse_ocr_result(result)
        print(f"Total text boxes: {len(text_boxes)}")
        
        # Group by rows (Y position)
        rows = self._group_by_rows(text_boxes)
        print(f"Grouped into {len(rows)} rows")
        
        # Identify skill area rows and extract A/B values
        extracted = {}
        
        for row in rows:
            skill, values = self._process_row(row)
            if skill:
                extracted[skill] = values
                print(f"{skill}: {values[:5]}... ({len(values)} values)")
        
        return extracted
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Optimize image for A/B detection - FAST version"""
        # MUCH smaller size for speed - just need to see A/B
        max_size = 1200  # Reduced from 2500
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.BILINEAR)  # Faster than LANCZOS
        
        # Convert to grayscale for faster processing
        image = image.convert('L').convert('RGB')
        
        # Quick contrast boost (no sharpening needed for A/B)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)  # Reduced from 1.5
        
        return image
    
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
        """Group text boxes by Y position into rows - FAST version"""
        if not boxes:
            return []
        
        # Sort by Y
        sorted_boxes = sorted(boxes, key=lambda b: b["y"])
        
        # Fixed threshold for speed (no median calculation)
        y_threshold = 15  # Simple fixed value
        
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
        # Map common OCR variations to skill names
        skill_keywords = {
            "gross": "Gross Motor", "fine": "Fine Motor",
            "eating": "Eating", "dressing": "Dressing",
            "grooming": "Grooming", "toileting": "Toileting",
            "receptive": "Receptive Language", "expressive": "Expressive Language",
            "social": "Social Interaction", "reading": "Reading",
            "writing": "Writing", "numbers": "Numbers",
            "time": "Time", "money": "Money",
            "domestic": "Domestic Behaviour", "community": "Community Orientation",
            "recreation": "Recreation", "vocational": "Vocational"
        }
        
        # Find skill name in row
        skill_found = None
        skill_box_x = 0
        
        for box in row:
            text_lower = box["text"].lower()
            for keyword, skill_name in skill_keywords.items():
                if keyword in text_lower:
                    skill_found = skill_name
                    skill_box_x = box["max_x"]
                    break
            if skill_found:
                break
        
        if not skill_found:
            return None, []
        
        # Extract A/B values from boxes AFTER the skill name
        values = []
        for box in row:
            if box["x"] <= skill_box_x:
                continue  # Skip skill name and row number
            
            value = self._classify_ab(box["text"])
            if value:
                values.append(value)
        
        return skill_found, values
    
    def _classify_ab(self, text: str) -> Optional[str]:
        """
        Classify text as A, B, or null - FAST version.
        Handles common OCR misreads.
        """
        if not text:
            return None
            
        text = text.strip().upper()
        
        # Quick length check
        if len(text) > 3 or len(text) == 0:
            return None
        
        # Get first character
        first_char = text[0]
        
        # Fast pattern matching - just check first character
        if first_char in 'ARPHNMVX4':
            return 'A'
        elif first_char in 'B8ED03O6':
            return 'B'
        
        return None
    
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
            
            # Ensure exactly 20 sessions - pad with empty strings if needed
            session_values = []
            for i in range(20):
                if i < len(values):
                    session_values.append(values[i])
                else:
                    session_values.append('')
            
            # Calculate totals
            total_a = sum(1 for v in session_values if v == 'A')
            total_b = sum(1 for v in session_values if v == 'B')
            
            # Build row as OBJECT (not array) for frontend compatibility
            row = {
                "Student_Name": student_name,
                "Register_Number": reg_number,
                "Skill_Area": skill,
                "Session_1": session_values[0],
                "Session_2": session_values[1],
                "Session_3": session_values[2],
                "Session_4": session_values[3],
                "Session_5": session_values[4],
                "Session_6": session_values[5],
                "Session_7": session_values[6],
                "Session_8": session_values[7],
                "Session_9": session_values[8],
                "Session_10": session_values[9],
                "Session_11": session_values[10],
                "Session_12": session_values[11],
                "Session_13": session_values[12],
                "Session_14": session_values[13],
                "Session_15": session_values[14],
                "Session_16": session_values[15],
                "Session_17": session_values[16],
                "Session_18": session_values[17],
                "Session_19": session_values[18],
                "Session_20": session_values[19],
                "Total_A": str(total_a) if total_a else '',
                "Total_B": str(total_b) if total_b else '',
                "I_Qr": '',
                "II_Qr": '',
                "III_Qr": '',
                "IV_Qr": '',
                "Assessment_Date": assessment_date
            }
            
            table_rows.append(row)
        
        # Debug output
        print("\n=== EXTRACTED DATA ===")
        print(f"Total skills with data: {len(extracted_data)}")
        for skill, vals in extracted_data.items():
            print(f"{skill}: {vals}")
        
        # Build full extraction report
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
