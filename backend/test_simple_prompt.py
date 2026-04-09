import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(__file__))

class MockReport:
    def __init__(self, goals_achieved, therapy_type):
        self.goals_achieved = goals_achieved
        self.therapy_type = therapy_type
        self.report_date = date(2026, 1, 14)

class MockStudent:
    def __init__(self, name):
        self.name = name

leo_goals = {
    "receptive_language": {
        "checked": True,
        "label": "Receptive Language Skills (Comprehension)",
        "notes": "Leo demonstrates strong progress in receptive language skills. He consistently follows 3-step commands across structured and play-based activities."
    },
    "expressive_language": {
        "checked": True,
        "label": "Expressive Language Skills",
        "notes": "Leo uses 4-5 word utterances spontaneously to express needs and describe actions."
    }
}

mock_report = MockReport(leo_goals, "Speech Therapy")
mock_student = MockStudent("Leo")

from app.api.endpoints.therapy_reports import _build_main_summary_prompt_with_fewshot

prompt = _build_main_summary_prompt_with_fewshot([mock_report], mock_student)
print(prompt)
