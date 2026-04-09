"""
Check which translation model is currently loaded
"""
import sys
sys.path.insert(0, 'C:\\Users\\renis\\OneDrive\\Desktop\\malu\\SSM-System\\backend')

from app.api.endpoints.translation import _translation_model, _tokenizer

print("="*60)
print("CURRENT TRANSLATION MODEL STATUS")
print("="*60)

print(f"\n_translation_model type: {type(_translation_model)}")
print(f"_tokenizer type: {type(_tokenizer)}")

if _translation_model is None:
    print("\n✓ No model loaded yet (will load on first request)")
elif isinstance(_translation_model, dict):
    print("\n⚠ Helsinki-NLP models are loaded")
    print(f"Loaded languages: {list(_translation_model.keys())}")
else:
    print("\n✓✓✓ IndicTrans2 model is loaded!")
    print(f"Model: {_translation_model}")

print("\n" + "="*60)
print("TO FIX: Restart the backend server:")
print("  1. Go to uvicorn terminal")
print("  2. Press Ctrl+C")
print("  3. Run: uvicorn app.main:app --reload")
print("="*60)
