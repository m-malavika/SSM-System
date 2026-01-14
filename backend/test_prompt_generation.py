"""
Test script to see exactly what prompt is being generated for the AI
"""
import sys
import os
from datetime import date

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

# Mock the therapy report and student objects
class MockReport:
    def __init__(self, goals_achieved, therapy_type, report_date):
        self.goals_achieved = goals_achieved
        self.therapy_type = therapy_type
        self.report_date = report_date
        self.progress_notes = ""

class MockStudent:
    def __init__(self, name):
        self.name = name

# Create test data matching the Cognitive Therapy test case
test_goals = {
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

# Create a mock report
mock_report = MockReport(
    goals_achieved=test_goals,
    therapy_type="Cognitive Therapy",
    report_date=date(2026, 1, 14)
)

mock_student = MockStudent("Test Child")

# Now import and call the prompt building function
from app.api.endpoints.therapy_reports import _build_main_summary_prompt_with_fewshot

print("=" * 100)
print("GENERATING PROMPT FOR AI MODEL")
print("=" * 100)
print()

# Generate the prompt
prompt = _build_main_summary_prompt_with_fewshot([mock_report], mock_student)

print(prompt)
print()
print("=" * 100)
print("END OF PROMPT")
print("=" * 100)
print()

# Check what data was extracted for each section
print("\n" + "=" * 100)
print("VERIFICATION: Checking if notes were extracted")
print("=" * 100)

therapy_sections = {
    "Cognitive Therapy": [
        "Attention & Concentration Skills",
        "Memory & Recall Skills",
        "Problem Solving & Reasoning Skills",
        "Executive Functioning Skills",
        "Cognitive Flexibility & Processing Skills"
    ]
}

for section_title in therapy_sections["Cognitive Therapy"]:
    # Count how many times this section appears in the prompt
    count = prompt.count(section_title)
    has_no_data = f"{section_title}:" in prompt and "[NO NOTES IN ANY REPORT FOR THIS SECTION]" in prompt
    
    print(f"\nSection: '{section_title}'")
    print(f"  Mentioned in prompt: {count} times")
    print(f"  Has 'NO NOTES' marker: {has_no_data}")
    
    # Find the section in the prompt and show what's there
    section_marker = f"{section_title}:"
    if section_marker in prompt:
        idx = prompt.index(section_marker)
        # Extract next 300 characters after the section title
        snippet = prompt[idx:idx+400]
        print(f"  Content preview: {snippet[:200]}...")
