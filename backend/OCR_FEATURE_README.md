# OCR Table Extraction Feature

## Overview
This feature allows you to upload images of student report tables and automatically extract the data using OCR (Optical Character Recognition).

## Installation

### 1. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Required for img2table)

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH (e.g., `C:\Program Files\Tesseract-OCR`)

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Verify installation:**
```bash
tesseract --version
```

## API Endpoint

### POST `/api/v1/students/upload-report`

Upload an image file containing a table to extract data.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Image file (JPG, PNG, BMP, TIFF)
- Max file size: 10MB

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/students/upload-report" \
  -H "accept: application/json" \
  -F "file=@/path/to/report.jpg"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/api/v1/students/upload-report"
files = {"file": open("report.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully extracted 1 table(s)",
  "method": "img2table",
  "filename": "report.jpg",
  "tables": [
    {
      "headers": ["Subject", "Marks", "Grade"],
      "rows": [
        {"Subject": "Math", "Marks": "95", "Grade": "A"},
        {"Subject": "Science", "Marks": "88", "Grade": "B"},
        {"Subject": "English", "Marks": "92", "Grade": "A"}
      ],
      "row_count": 3
    }
  ]
}
```

## How It Works

The service uses two OCR methods:

1. **img2table (Primary)**: Better for structured tables with clear borders
2. **PaddleOCR (Fallback)**: Used if img2table doesn't detect tables

### OCR Process:
1. Image is uploaded and validated
2. img2table attempts to detect and extract structured tables
3. If no tables found, PaddleOCR extracts text and groups it into rows/columns
4. Data is returned as JSON with headers and rows

## Frontend Integration Example

```javascript
// In your React component
const handleImageUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/students/upload-report', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success && data.tables.length > 0) {
      // Display the extracted table
      const table = data.tables[0];
      console.log('Headers:', table.headers);
      console.log('Rows:', table.rows);
      
      // You can now populate a grid/table component with this data
      setTableData(table.rows);
    }
  } catch (error) {
    console.error('OCR failed:', error);
  }
};
```

## Supported Image Formats
- JPEG/JPG
- PNG
- BMP
- TIFF

## Tips for Best Results

1. **Image Quality**: Use high-resolution images (at least 300 DPI)
2. **Table Structure**: Clear borders and separation between cells work best
3. **Lighting**: Ensure good contrast between text and background
4. **Orientation**: Image should be properly oriented (not rotated)
5. **File Size**: Keep under 10MB for faster processing

## Troubleshooting

### "Tesseract not found" error
- Make sure Tesseract is installed and in your system PATH
- Windows: Add `C:\Program Files\Tesseract-OCR` to PATH
- Restart your terminal/IDE after installation

### Poor extraction accuracy
- Try improving image quality
- Ensure the table has clear borders
- Check that text is not too small or blurry
- Try a different image format (PNG usually works best)

### "No tables detected"
- The image may not contain a recognizable table structure
- Try adding borders to your table before capturing the image
- Ensure sufficient contrast between table lines and background

## Performance Notes

- First request may be slower (loading OCR models)
- Subsequent requests are faster (models cached in memory)
- Processing time depends on image size and complexity
- Typical processing time: 2-10 seconds per image

## Libraries Used

- **PaddleOCR**: Deep learning-based OCR engine
- **img2table**: Table detection and extraction
- **Tesseract**: OCR engine (used by img2table)
- **Pillow**: Image processing
- **OpenCV**: Image manipulation

All libraries are free and open-source!
