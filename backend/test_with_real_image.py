"""
Test OCR with the provided assessment form image
This script helps you test the enhanced OCR with your actual assessment form
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.ocr_service import ocr_service
from PIL import Image
import json


def save_preprocessed_image(input_path: str, output_path: str = "preprocessed_output.jpg"):
    """
    Save preprocessed version of the image to see what OCR sees
    """
    print(f"\n--- Preprocessing Image ---")
    print(f"Input: {input_path}")
    
    # Read image
    img = Image.open(input_path)
    print(f"Original size: {img.size}")
    
    # Preprocess
    preprocessed = ocr_service._preprocess_image(img)
    print(f"Preprocessed size: {preprocessed.size}")
    
    # Save
    preprocessed.save(output_path)
    print(f"Saved preprocessed image to: {output_path}")
    print("✓ You can view this to see how the image was enhanced\n")


def analyze_extraction(result: dict):
    """
    Detailed analysis of extraction results
    """
    print("\n" + "="*80)
    print(" DETAILED EXTRACTION ANALYSIS")
    print("="*80 + "\n")
    
    if not result.get('success'):
        print(f"❌ Extraction failed: {result.get('error')}")
        return
    
    extracted_data = result.get('extracted_data', {})
    
    # Overall statistics
    total_values = sum(len(values) for values in extracted_data.values())
    total_a = sum(values.count('A') for values in extracted_data.values())
    total_b = sum(values.count('B') for values in extracted_data.values())
    total_empty = sum(values.count('') for values in extracted_data.values())
    
    print(f"📊 OVERALL STATISTICS")
    print(f"   Skills detected: {len(extracted_data)}/18")
    print(f"   Total cells: {total_values}")
    print(f"   A values: {total_a} ({total_a/total_values*100:.1f}%)")
    print(f"   B values: {total_b} ({total_b/total_values*100:.1f}%)")
    print(f"   Empty cells: {total_empty} ({total_empty/total_values*100:.1f}%)")
    
    # Per-skill analysis
    print(f"\n📋 PER-SKILL BREAKDOWN")
    print(f"{'Skill Area':<25} | A's | B's | Empty | Fill% | Pattern")
    print("-" * 85)
    
    for skill, values in extracted_data.items():
        a_count = values.count('A')
        b_count = values.count('B')
        empty_count = values.count('')
        filled = 20 - empty_count
        fill_rate = (filled / 20) * 100
        
        # Create pattern visualization
        pattern = ''.join(['A' if v == 'A' else 'B' if v == 'B' else '·' for v in values[:20]])
        
        print(f"{skill:<25} | {a_count:3d} | {b_count:3d} | {empty_count:5d} | {fill_rate:4.0f}% | {pattern}")
    
    # Data quality assessment
    print(f"\n✨ DATA QUALITY ASSESSMENT")
    
    skills_with_data = sum(1 for v in extracted_data.values() if any(x in ['A', 'B'] for x in v))
    coverage = skills_with_data / 18 * 100
    
    print(f"   Coverage: {skills_with_data}/18 skills ({coverage:.1f}%)")
    
    if coverage >= 90:
        print(f"   Rating: ⭐⭐⭐⭐⭐ Excellent")
    elif coverage >= 75:
        print(f"   Rating: ⭐⭐⭐⭐ Good")
    elif coverage >= 50:
        print(f"   Rating: ⭐⭐⭐ Fair")
    else:
        print(f"   Rating: ⭐⭐ Needs Improvement")
    
    # Missing skills
    expected_skills = [
        "Gross Motor", "Fine Motor", "Eating", "Dressing", "Grooming",
        "Toileting", "Receptive Language", "Expressive Language", 
        "Social Interaction", "Reading", "Writing", "Numbers",
        "Time", "Money", "Domestic Behaviour", "Community Orientation",
        "Recreation", "Vocational"
    ]
    
    missing_skills = [s for s in expected_skills if s not in extracted_data or 
                     not any(x in ['A', 'B'] for x in extracted_data.get(s, []))]
    
    if missing_skills:
        print(f"\n   ⚠ Missing or empty skills ({len(missing_skills)}):")
        for skill in missing_skills:
            print(f"      - {skill}")
    else:
        print(f"\n   ✓ All 18 skills extracted successfully!")
    
    print()


def main():
    """
    Main test function - modify image_path to your image location
    """
    print("\n" + "="*80)
    print(" TESTING OCR WITH YOUR ASSESSMENT FORM")
    print("="*80 + "\n")
    
    # === MODIFY THIS PATH TO YOUR IMAGE ===
    image_path = "assessment_form.jpg"  # Change this to your image path
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        print(f"\n💡 How to use this script:")
        print(f"   1. Save your assessment form image in the backend folder")
        print(f"   2. Name it 'assessment_form.jpg' (or update the script)")
        print(f"   3. Run: python test_with_real_image.py\n")
        
        # Try to find image in current directory
        print(f"Looking for images in current directory...")
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            files = list(Path('.').glob(f'*{ext}'))
            if files:
                print(f"Found {ext} files:")
                for f in files[:5]:  # Show first 5
                    print(f"   - {f}")
        
        return
    
    # Step 1: Save preprocessed image
    print("STEP 1: Preprocessing Image")
    save_preprocessed_image(image_path)
    
    # Step 2: Run OCR extraction
    print("\nSTEP 2: Running OCR Extraction")
    with open(image_path, 'rb') as f:
        file_bytes = f.read()
    
    print(f"Image size: {len(file_bytes):,} bytes")
    print("Processing... (this may take 3-5 seconds)\n")
    
    result = ocr_service.extract_table_from_image(file_bytes)
    
    # Step 3: Analyze results
    print("\nSTEP 3: Analyzing Results")
    analyze_extraction(result)
    
    # Step 4: Save results
    output_file = 'extraction_results.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "="*80)
    print(" FILES GENERATED")
    print("="*80)
    print(f"   ✓ {output_file} - Full extraction results (JSON)")
    print(f"   ✓ preprocessed_output.jpg - Preprocessed image")
    print("\n" + "="*80)
    print(" TESTING COMPLETE")
    print("="*80 + "\n")
    
    # Recommendations
    print("💡 NEXT STEPS:")
    print("   1. Check preprocessed_output.jpg - is text clear?")
    print("   2. Review extraction_results.json for accuracy")
    print("   3. If accuracy is low:")
    print("      - Rescan at higher DPI (400-600)")
    print("      - Ensure better lighting/contrast")
    print("      - Check that table grid lines are visible")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Custom image path provided
        image_path = sys.argv[1]
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            sys.exit(1)
        
        print(f"\nTesting with: {image_path}\n")
        save_preprocessed_image(image_path)
        
        with open(image_path, 'rb') as f:
            file_bytes = f.read()
        
        result = ocr_service.extract_table_from_image(file_bytes)
        analyze_extraction(result)
        
        with open('extraction_results.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print("\n✓ Results saved to extraction_results.json\n")
    else:
        main()
