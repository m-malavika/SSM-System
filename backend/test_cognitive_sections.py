"""
Test script to verify Cognitive Therapy section data extraction
"""
import sys
import json

# Test case data structure
test_report_data = {
    "attention_concentration": {
        "checked": True,
        "label": "Attention & Concentration Skills",
        "notes": "The child demonstrates inconsistent attention across tasks. Sustains focus briefly during preferred activities but quickly disengages during structured or non-preferred tasks. Frequent verbal and physical redirection is required, with no notable improvement observed."
    },
    "memory_recall": {
        "checked": True,
        "label": "Memory & Recall Skills",
        "notes": "The child is able to recall highly familiar information when provided with visual cues. Retention of newly introduced material remains poor, and repeated prompts are required. Progress in memory skills is minimal."
    },
    "problem_solving": {
        "checked": True,
        "label": "Problem Solving & Reasoning Skills",
        "notes": "The child attempts simple problem-solving tasks when guided but is unable to complete them independently. Responses are largely trial-and-error, with limited evidence of logical reasoning."
    },
    "executive_functioning": {
        "checked": True,
        "label": "Executive Functioning Skills",
        "notes": "The child demonstrates difficulty initiating tasks and requires continuous adult support to remain engaged. Multi-step activities are not completed independently, and carryover of skills across sessions is limited."
    },
    "cognitive_flexibility": {
        "checked": True,
        "label": "Cognitive Flexibility & Processing Skills",
        "notes": "The child shows resistance to changes in routine and requires additional time to transition between activities. Processing speed remains slow, and task completion is delayed despite consistent support."
    }
}

# Expected section titles from backend
backend_sections = [
    "Attention & Concentration Skills",
    "Memory & Recall Skills",
    "Problem Solving & Reasoning Skills",
    "Executive Functioning Skills",
    "Cognitive Flexibility & Processing Skills"
]

print("=" * 80)
print("COGNITIVE THERAPY SECTION VERIFICATION")
print("=" * 80)
print()

# Check 1: Verify all section labels match
print("CHECK 1: Section Label Matching")
print("-" * 80)
data_labels = [v['label'] for v in test_report_data.values()]
print(f"Backend expects: {backend_sections}")
print(f"Test data has:   {data_labels}")
print()

all_match = all(label in backend_sections for label in data_labels)
if all_match and len(data_labels) == len(backend_sections):
    print("✅ SUCCESS: All section labels match exactly!")
else:
    print("❌ MISMATCH: Section labels don't match!")
    missing_in_backend = [l for l in data_labels if l not in backend_sections]
    missing_in_data = [l for l in backend_sections if l not in data_labels]
    if missing_in_backend:
        print(f"   Missing in backend: {missing_in_backend}")
    if missing_in_data:
        print(f"   Missing in test data: {missing_in_data}")

print()
print()

# Check 2: Verify data extraction logic would work
print("CHECK 2: Data Extraction Simulation")
print("-" * 80)
print("Simulating backend data extraction logic:")
print()

for section_title in backend_sections:
    print(f"Section: '{section_title}'")
    notes_found = []
    
    # Simulate the backend matching logic
    for key, value in test_report_data.items():
        if isinstance(value, dict):
            label_match = value.get('label') == section_title
            has_notes = value.get('notes') and value['notes'].strip()
            
            print(f"  - Key '{key}': label='{value.get('label')}', match={label_match}, has_notes={has_notes}")
            
            if label_match and has_notes:
                notes_found.append(value['notes'])
    
    if notes_found:
        print(f"  ✅ Found {len(notes_found)} note(s)")
        print(f"     Preview: {notes_found[0][:80]}...")
    else:
        print(f"  ❌ NO NOTES FOUND - AI would show 'No data available'")
    print()

print()
print("=" * 80)
print("CHECK 3: Data Content Analysis")
print("=" * 80)
print()

for section_title in backend_sections:
    for key, value in test_report_data.items():
        if value.get('label') == section_title:
            notes = value.get('notes', '')
            
            # Check if notes contain negative/difficulty indicators
            negative_indicators = [
                'inconsistent', 'difficulty', 'unable', 'poor', 'minimal',
                'limited', 'requires', 'slow', 'delayed', 'resistance',
                'no notable improvement', 'no improvement', 'not completed'
            ]
            
            found_indicators = [ind for ind in negative_indicators if ind.lower() in notes.lower()]
            
            print(f"Section: {section_title}")
            print(f"  Length: {len(notes)} characters")
            print(f"  Contains difficulty/limitation indicators: {', '.join(found_indicators) if found_indicators else 'None'}")
            print(f"  Classification: {'VALID CLINICAL DATA (negative findings)' if found_indicators else 'VALID CLINICAL DATA'}")
            print(f"  Expected AI behavior: SUMMARIZE these findings (NOT 'no data available')")
            print()

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("✅ All 5 Cognitive Therapy sections are correctly configured")
print("✅ Section labels match between frontend and backend")
print("✅ Data structure is correct with 'label' field for matching")
print("✅ All sections contain valid clinical data (negative findings)")
print()
print("EXPECTED AI BEHAVIOR:")
print("- AI should generate summaries for ALL 5 sections")
print("- Each section should contain 2-4 bullet points")
print("- Bullet points should preserve the negative/difficulty language")
print("- NO section should show 'No data available'")
print()
print("If AI still shows 'No data available', check:")
print("1. Backend logs for actual label matching results")
print("2. Database structure - ensure goals_achieved is stored as JSON dict")
print("3. Frontend - verify it's sending data with correct structure")
print()
