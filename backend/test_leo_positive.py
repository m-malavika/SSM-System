"""
Test with Leo's POSITIVE Speech Therapy notes to ensure tone is preserved
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

class MockReport:
    def __init__(self, goals_achieved, therapy_type, report_date):
        self.goals_achieved = goals_achieved
        self.therapy_type = therapy_type
        self.report_date = report_date
        self.progress_notes = ""

class MockStudent:
    def __init__(self, name):
        self.name = name

# Create Leo's POSITIVE test data
leo_goals = {
    "receptive_language": {
        "checked": True,
        "label": "Receptive Language Skills (Comprehension)",
        "notes": "Leo demonstrates strong progress in receptive language skills. He consistently follows 3-step commands across structured and play-based activities, comprehends basic prepositions reliably, and recognizes personal pronouns with minimal to no support."
    },
    "expressive_language": {
        "checked": True,
        "label": "Expressive Language Skills",
        "notes": "Leo uses 4–5 word utterances spontaneously to express needs and describe actions. He is able to retell simple multi-event stories using picture cues, requiring minimal to moderate assistance depending on task complexity."
    },
    "oral_motor_opt": {
        "checked": True,
        "label": "Oral Motor & Oral Placement Therapy (OPT) Goals",
        "notes": "Leo shows steady improvement in oral motor skills, including lip closure, jaw stability, and tongue movements. He participates actively in oral motor exercises and requires reduced cueing across sessions."
    },
    "pragmatic_language": {
        "checked": True,
        "label": "Pragmatic Language Skills (Social Communication)",
        "notes": "Leo engages in reciprocal communication and maintains 2–3 turn exchanges with adults and peers. Use of greetings, comments, and simple emotional expressions is consistent, with emerging appropriateness in interactions with unfamiliar individuals."
    },
    "narrative_skills": {
        "checked": True,
        "label": "Narrative Skills",
        "notes": "Leo demonstrates clear progress in narrative development. He sequences 3–5 picture cards accurately and narrates events meaningfully, showing increased enjoyment and confidence in storytelling tasks."
    }
}

mock_report = MockReport(
    goals_achieved=leo_goals,
    therapy_type="Speech Therapy",
    report_date=date(2026, 1, 14)
)

mock_student = MockStudent("Leo")

from app.api.endpoints.therapy_reports import _build_main_summary_prompt_with_fewshot

print("=" * 100)
print("TESTING WITH LEO'S POSITIVE SPEECH THERAPY NOTES")
print("=" * 100)
print()

prompt = _build_main_summary_prompt_with_fewshot([mock_report], mock_student)

# Check for key indicators
print("CHECKING PROMPT CONTENT:")
print("-" * 100)
print()

# Check if positive example is included
if "demonstrates strong progress" in prompt.lower():
    print("[OK] Positive example is included in prompt")
else:
    print("[FAIL] Positive example NOT found in prompt")

# Check for mutual exclusion rule
if "MUTUAL EXCLUSION" in prompt:
    print("[OK] Mutual exclusion rule is present")
else:
    print("[FAIL] Mutual exclusion rule NOT found")

# Check for tone matching rule
if "TONE MATCHING" in prompt:
    print("[OK] Tone matching rule is present")
else:
    print("[FAIL] Tone matching rule NOT found")

# Check if Leo's notes are included
if "Leo demonstrates strong progress in receptive language" in prompt:
    print("[OK] Leo's receptive language notes found")
else:
    print("[FAIL] Leo's receptive language notes NOT found")

if "uses 4–5 word utterances spontaneously" in prompt:
    print("[OK] Leo's expressive language notes found")  
else:
    print("[FAIL] Leo's expressive language notes NOT found")

# Check for fabrication warnings
if "Do NOT add words like 'refuses', 'struggles', 'difficulty'" in prompt:
    print("[OK] Fabrication warning present")
else:
    print("[FAIL] Fabrication warning NOT found")

print()
print("-" * 100)
print("EXPECTED AI BEHAVIOR:")
print("-" * 100)
print("The AI should generate a summary that:")
print("1. Uses POSITIVE language matching the input")
print("2. Says 'demonstrates strong progress', 'consistently follows', etc.")
print("3. Does NOT say 'refuses', 'struggles', 'difficulty'")
print("4. Does NOT include 'No data available' (all sections have notes)")
print("5. Does NOT invert positive findings into negative")
print()

# Show a snippet of the critical instruction
print("CRITICAL INSTRUCTION SECTION:")
print("-" * 100)
if "*** CRITICAL INSTRUCTION" in prompt:
    idx = prompt.index("*** CRITICAL INSTRUCTION")
    snippet = prompt[idx:idx+800]
    print(snippet)
else:
    print("[FAIL] Critical instruction not found!")
