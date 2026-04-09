# Translation Feature - IndicTrans2 Integration

## Overview
The translation feature allows users to translate AI-generated therapy report summaries from English to various Indian languages using **IndicTrans2** by AI4Bharat.

## Supported Languages

| Language | Code | Native Name |
|----------|------|-------------|
| Malayalam | mal_Mlym | മലയാളം |
| Hindi | hin_Deva | हिन्दी |
| Tamil | tam_Tamil | தமிழ் |
| Telugu | tel_Telu | తెలుగు |
| Kannada | kan_Knda | ಕನ್ನಡ |
| Bengali | ben_Beng | বাংলা |
| Gujarati | guj_Gujr | ગુજરાતી |
| Marathi | mar_Deva | मराठी |
| Punjabi | pan_Guru | ਪੰਜਾਬੀ |
| Odia | ory_Orya | ଓଡ଼ିଆ |

## How It Works

### Frontend (StudentPage.jsx)
1. Click the **Translate** button (globe icon) next to the Summary button in the Progress Summary section
2. Select your target language from the dropdown modal
3. The system sends a translation request to the backend
4. Displays the translated summary with option to view original

### Backend (translation.py)
1. Receives translation request with text and target language
2. Lazy loads IndicTrans2 model (1B parameter model for English to Indic languages)
3. Processes the text through the model
4. Returns translated text

## Installation

### Backend Dependencies
```bash
cd backend
pip install transformers torch sentencepiece sacremoses
```

These are already added to `requirements.txt`:
- transformers>=4.35.0
- torch>=2.0.0
- sentencepiece>=0.1.99
- sacremoses>=0.0.53

### Model Download
The IndicTrans2 model (~2GB) is downloaded automatically on first use from Hugging Face Hub:
- Model: `ai4bharat/indictrans2-en-indic-1B`

## API Endpoint

### POST /api/v1/translate
Translate text from English to Indian languages

**Request Body:**
```json
{
  "text": "The student showed improvement in communication skills.",
  "target_language": "mal_Mlym",
  "source_language": "eng_Latn"
}
```

**Response:**
```json
{
  "translated_text": "വിദ്യാർത്ഥി ആശയവിനിമയ കഴിവുകളിൽ പുരോഗതി കാണിച്ചു.",
  "source_language": "eng_Latn",
  "target_language": "mal_Mlym"
}
```

**Headers:**
- Authorization: Bearer {token}
- Content-Type: application/json

## Testing

Run the test script:
```bash
cd backend
python test_translation.py
```

Update credentials in the test file as needed.

## Performance Notes

- **First Request**: Takes longer (~30-60 seconds) as model loads into memory
- **Subsequent Requests**: Much faster (~2-5 seconds) as model stays in memory
- **GPU Support**: Automatically uses CUDA if available for faster translation
- **Memory**: Requires ~4GB RAM for model in memory

## UI Features

1. **Language Selector Modal**: Displays language names in both English and native scripts
2. **Translation Progress**: Shows loading animation during translation
3. **Bilingual View**: Switch between original and translated text
4. **Visual Feedback**: Active states on button clicks

## Technical Details

- **Model**: IndicTrans2-en-indic-1B (AI4Bharat)
- **Architecture**: Transformer-based sequence-to-sequence model
- **Input Length**: Max 512 tokens
- **Beam Search**: Uses 5 beams for better translation quality
- **Lazy Loading**: Model loads only when first translation is requested

## Troubleshooting

1. **Model Loading Error**: Ensure internet connection for first-time download
2. **Out of Memory**: Close other applications or use smaller batch sizes
3. **Slow Translation**: First request loads model; subsequent requests are faster
4. **Network Error**: Check backend server is running and API endpoint is accessible

## Future Enhancements

- [ ] Support for Indic-to-Indic translation
- [ ] Batch translation for multiple sections
- [ ] Translation history/caching
- [ ] Offline mode with pre-downloaded models
- [ ] Support for more Indian languages
- [ ] PDF export with translated content
