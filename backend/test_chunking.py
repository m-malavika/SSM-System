"""Quick test of chunking approach"""
import re

text = """The student has demonstrated consistent progress across multiple therapy sessions during this evaluation period. 

Communication skills have shown significant improvement, with the student now able to express basic needs more clearly and respond appropriately to simple verbal cues. The student's receptive language abilities have developed notably, showing better comprehension of instructions and environmental sounds.

Social interaction skills continue to develop steadily. The student is beginning to show more interest in peer activities and demonstrates improved eye contact during structured sessions. Turn-taking behaviors have improved, particularly during preferred activities.

Fine motor skills show gradual progress. The student can now hold writing instruments with better grip control and complete simple drawing tasks with minimal assistance. Self-care activities like buttoning and zipping have also shown improvement.

Continued focus on maintaining and expanding communication abilities is recommended. Incorporating more peer interaction opportunities and practicing self-care routines in natural settings will support further development. The family is encouraged to continue reinforcement strategies at home for optimal progress."""

# Split into sentences
sentences = re.split(r'(?<=[.!?])\s+', text)

print(f"Original text: {len(text)} characters")
print(f"Sentences found: {len(sentences)}")
print()

for i, sent in enumerate(sentences, 1):
    print(f"{i}. [{len(sent)} chars] {sent[:50]}...")
