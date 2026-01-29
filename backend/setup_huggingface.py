"""
Login to HuggingFace and configure IndicTrans2 access
"""
from huggingface_hub import login
import os

print("=" * 60)
print("HUGGINGFACE LOGIN - IndicTrans2 Setup")
print("=" * 60)
print()
print("Steps you should have completed:")
print("1. ✓ Go to https://huggingface.co/ai4bharat/indictrans2-en-indic-1B")
print("2. ✓ Click 'Request access' and wait for approval")
print("3. ✓ Go to https://huggingface.co/settings/tokens")
print("4. ✓ Create a new 'Read' token")
print()
print("=" * 60)
print()

token = input("Paste your HuggingFace token here: ").strip()

if not token:
    print("❌ No token provided. Exiting.")
    exit(1)

try:
    print("\n🔄 Logging in to HuggingFace...")
    login(token=token, add_to_git_credential=True)
    print("✅ Successfully logged in to HuggingFace!")
    print()
    print("Next steps:")
    print("1. The translation endpoint will now use IndicTrans2")
    print("2. Test it by clicking the Translate button in your app")
    print("3. First translation will download the model (~2GB)")
    print()
    
    # Save token to environment file
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # Read existing content
    env_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Remove any existing HuggingFace token lines
    lines = env_content.split('\n')
    lines = [line for line in lines if not line.startswith('HUGGINGFACE')]
    
    # Add the correct token
    lines.append(f"\n# Hugging Face API Token")
    lines.append(f"HUGGINGFACE_API_TOKEN={token}")
    
    # Write back
    with open(env_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Token saved to {env_file}")
    
except Exception as e:
    print(f"❌ Login failed: {e}")
    print()
    print("Troubleshooting:")
    print("- Verify your token is correct")
    print("- Ensure you have access to indictrans2-en-indic-1B")
    print("- Check your internet connection")
