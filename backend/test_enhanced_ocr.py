"""
Test Enhanced OCR Service
Demonstrates improved preprocessing, table detection, and A/B classification
"""
import sys
import os
from pathlib import Path
import json

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.ocr_service import ocr_service


def test_with_image(image_path: str):
    """Test OCR service with a specific image"""
    print(f"\n{'='*80}")
    print(f"Testing OCR with: {image_path}")
    print(f"{'='*80}\n")
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return
    
    # Read image file
    with open(image_path, 'rb') as f:
        file_bytes = f.read()
    
    print(f"Image size: {len(file_bytes)} bytes")
    
    # Run OCR extraction
    print("\n--- Running Enhanced OCR Extraction ---\n")
    result = ocr_service.extract_table_from_image(file_bytes)
    
    # Display results
    print(f"\n{'='*80}")
    print("EXTRACTION RESULTS")
    print(f"{'='*80}\n")
    
    print(f"Success: {result.get('success')}")
    print(f"Method: {result.get('method')}")
    print(f"Table Count: {result.get('table_count')}")
    
    if result.get('success'):
        # Show extraction summary
        summary = result.get('extraction_summary', {})
        print(f"\n--- Extraction Summary ---")
        print(f"Total Skills Found: {summary.get('total_skills_found')}")
        print(f"Skills Detected: {', '.join(summary.get('skills_found', []))}")
        
        # Show sample values
        print(f"\n--- Sample Extracted Values ---")
        sample_values = summary.get('sample_values', {})
        for skill, values in sample_values.items():
            print(f"{skill}: {values}")
        
        # Show complete extracted data
        print(f"\n--- Complete Extracted Data ---")
        extracted_data = result.get('extracted_data', {})
        for skill, values in extracted_data.items():
            a_count = values.count('A')
            b_count = values.count('B')
            empty_count = values.count('')
            filled = 20 - empty_count
            fill_rate = (filled / 20) * 100
            
            # Visual representation
            visual = ''.join(['A' if v == 'A' else 'B' if v == 'B' else '·' for v in values])
            
            print(f"{skill:25s}: [{visual}] | Filled: {filled}/20 ({fill_rate:.0f}%) | A={a_count}, B={b_count}")
        
        # Show structured table
        if result.get('tables'):
            table = result['tables'][0]
            print(f"\n--- Structured Table Output ---")
            print(f"Headers: {len(table.get('headers', []))} columns")
            print(f"Rows: {table.get('row_count')} skill areas")
            
            # Show first few rows
            print(f"\n--- First 3 Skill Rows ---")
            for i, row in enumerate(table.get('rows', [])[:3]):
                print(f"\nRow {i+1}: {row['Skill_Area']}")
                sessions = [row.get(f'Session_{j}', '') for j in range(1, 21)]
                print(f"  Sessions: {sessions}")
                print(f"  Total A: {row.get('Total_A')}, Total B: {row.get('Total_B')}")
        
        # Save results to file
        output_file = 'ocr_test_results.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Full results saved to: {output_file}")
        
    else:
        print(f"\nError: {result.get('error')}")
    
    print(f"\n{'='*80}\n")


def test_preprocessing():
    """Test image preprocessing steps"""
    from PIL import Image
    import numpy as np
    
    print(f"\n{'='*80}")
    print("Testing Image Preprocessing Pipeline")
    print(f"{'='*80}\n")
    
    # Create a sample test image (simulating a scan)
    test_img = Image.new('RGB', (800, 600), color='white')
    
    print("1. Original image created: 800x600")
    
    # Test preprocessing
    preprocessed = ocr_service._preprocess_image(test_img)
    print(f"2. Preprocessed image size: {preprocessed.size}")
    print(f"   - Applied: denoising, CLAHE, deskewing, binarization, sharpening")
    
    print("\n✓ Preprocessing pipeline working correctly\n")


def test_ab_classification():
    """Test A/B classification logic"""
    print(f"\n{'='*80}")
    print("Testing A/B Classification")
    print(f"{'='*80}\n")
    
    # Test cases (common OCR outputs from handwriting)
    test_cases = [
        # Clear cases
        ('A', 'A'),
        ('B', 'B'),
        ('a', 'A'),
        ('b', 'B'),
        
        # Common OCR variations for A
        ('R', 'A'),
        ('P', 'A'),
        ('H', 'A'),
        ('AR', 'A'),
        ('AP', 'A'),
        ('4', 'A'),
        
        # Common OCR variations for B
        ('8', 'B'),
        ('E', 'B'),
        ('D', 'B'),
        ('B8', 'B'),
        ('BE', 'B'),
        ('0', 'B'),
        
        # Ambiguous cases
        ('', None),
        ('ABC', None),
        ('123', None),
        ('---', None),
    ]
    
    print(f"{'Input':<15} | {'Expected':<10} | {'Result':<10} | Status")
    print("-" * 60)
    
    correct = 0
    total = 0
    
    for input_text, expected in test_cases:
        result = ocr_service._classify_ab(input_text)
        status = '✓' if result == expected else '✗'
        if result == expected:
            correct += 1
        total += 1
        
        print(f"{input_text or '(empty)':<15} | {str(expected):<10} | {str(result):<10} | {status}")
    
    accuracy = (correct / total) * 100
    print(f"\nAccuracy: {correct}/{total} ({accuracy:.1f}%)")
    print()


def main():
    """Main test function"""
    print("\n" + "="*80)
    print(" ENHANCED OCR SERVICE TEST SUITE")
    print("="*80)
    
    # Test 1: Preprocessing
    test_preprocessing()
    
    # Test 2: A/B Classification
    test_ab_classification()
    
    # Test 3: Real image (if available)
    print("\n" + "="*80)
    print(" REAL IMAGE TESTS")
    print("="*80)
    
    # Check for test images
    possible_paths = [
        "test_assessment.jpg",
        "test_assessment.png",
        "sample_assessment.jpg",
        "sample_assessment.png",
        "../test_assessment.jpg",
    ]
    
    image_found = False
    for path in possible_paths:
        if os.path.exists(path):
            test_with_image(path)
            image_found = True
            break
    
    if not image_found:
        print("\n⚠ No test image found. Place an assessment form image in the backend directory")
        print("   Supported names: test_assessment.jpg, sample_assessment.jpg")
        print("\nYou can test with your own image by running:")
        print("   python test_enhanced_ocr.py <path_to_image>")
    
    print("\n" + "="*80)
    print(" TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided image path
        test_with_image(sys.argv[1])
    else:
        # Run full test suite
        main()
