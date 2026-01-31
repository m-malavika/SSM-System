"""
Translation endpoint using NLLB-200 for Malayalam and Helsinki-NLP for other Indian languages
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/clear-translation-cache")
async def clear_translation_cache(current_user: User = Depends(get_current_user)):
    """Force clear translation models cache - requires restart to take effect"""
    global _translation_model, _tokenizer, _nllb_model, _nllb_tokenizer
    
    old_type = "NLLB/Helsinki" if _translation_model or _nllb_model else "None"
    
    _translation_model = None
    _tokenizer = None
    _nllb_model = None
    _nllb_tokenizer = None
    
    logger.info(f"Translation model cache cleared (was: {old_type})")
    return {
        "status": "success",
        "message": "Translation cache cleared. Models will reload on next request.",
        "previous_model": old_type
    }

# Translation request model
class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: str = "eng_Latn"  # Default source is English

class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str

# Lazy load the translation models
_translation_model = None
_tokenizer = None
_nllb_model = None
_nllb_tokenizer = None

def get_nllb_model():
    """
    Lazy load Facebook NLLB-200-distilled-600M model for Malayalam translation
    """
    global _nllb_model, _nllb_tokenizer
    
    if _nllb_model is None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch
        
        model_name = "facebook/nllb-200-distilled-600M"
        logger.info(f"Loading NLLB model: {model_name}")
        
        _nllb_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _nllb_model = _nllb_model.to(device)
        logger.info(f"✓ NLLB-200 model loaded on {device}")
    
    return _nllb_model, _nllb_tokenizer

def get_translation_model():
    """
    Lazy load translation model - uses Helsinki-NLP for non-Malayalam languages
    """
    global _translation_model, _tokenizer
    
    if _translation_model is None:
        logger.info("Using Helsinki-NLP models for translation (non-Malayalam)")
        _translation_model = {}
        _tokenizer = {}
        logger.info("✓ Translation models ready (Helsinki-NLP)")
        return _translation_model, _tokenizer, "helsinki"
    
    logger.debug("Using Helsinki-NLP models")
    return _translation_model, _tokenizer, "helsinki"

def get_model_for_language(target_lang):
    """Get or load the appropriate model for the target language (non-Malayalam)"""
    from transformers import MarianMTModel, MarianTokenizer
    import torch
    
    global _translation_model, _tokenizer
    
    if _translation_model is None:
        _translation_model = {}
        _tokenizer = {}
    
    # Model mapping for each language (excluding Malayalam - uses NLLB)
    model_map = {
        "hi": "Helsinki-NLP/opus-mt-en-hi",  # Hindi
        "bn": "Helsinki-NLP/opus-mt-en-bn",  # Bengali  
        "ta": "Helsinki-NLP/opus-mt-en-ta",  # Tamil
        "te": "Helsinki-NLP/opus-mt-en-te",  # Telugu
        "mr": "Helsinki-NLP/opus-mt-en-mr",  # Marathi
        "gu": "Helsinki-NLP/opus-mt-en-gu",  # Gujarati
        # Fallback for others
        "default": "Helsinki-NLP/opus-mt-en-mul"
    }
    
    model_name = model_map.get(target_lang, model_map["default"])
    
    # Load model if not cached
    if target_lang not in _translation_model:
        logger.info(f"Loading model for {target_lang}: {model_name}")
        _tokenizer[target_lang] = MarianTokenizer.from_pretrained(model_name)
        _translation_model[target_lang] = MarianMTModel.from_pretrained(model_name)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _translation_model[target_lang] = _translation_model[target_lang].to(device)
        logger.info(f"Model for {target_lang} loaded on {device}")
    
    return _translation_model[target_lang], _tokenizer[target_lang]

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Translate text from English to Indian languages
    
    Supported language codes:
    - mal_Mlym: Malayalam (ml) - Uses Facebook NLLB-200-distilled-600M
    - hin_Deva: Hindi (hi) - Uses Helsinki-NLP
    - tam_Tamil: Tamil (ta) - Uses Helsinki-NLP
    - tel_Telu: Telugu (te) - Uses Helsinki-NLP
    - kan_Knda: Kannada (kn) - Uses Helsinki-NLP
    - ben_Beng: Bengali (bn) - Uses Helsinki-NLP
    - guj_Gujr: Gujarati (gu) - Uses Helsinki-NLP
    - mar_Deva: Marathi (mr) - Uses Helsinki-NLP
    - pan_Guru: Punjabi (pa) - Uses Helsinki-NLP
    - ory_Orya: Odia (or) - Uses Helsinki-NLP
    """
    try:
        logger.info(f"Translation request from user {current_user.username} to {request.target_language}")
        logger.info(f"Text length: {len(request.text)} characters")
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Validate text length (AI summaries are typically 100-2000 chars)
        if len(request.text) > 5000:
            logger.warning(f"Large text received: {len(request.text)} chars")
            # Truncate if too large
            request.text = request.text[:5000]
            logger.info("Text truncated to 5000 characters")
        
        # Map IndicTrans2 language codes to ISO codes
        language_map = {
            "mal_Mlym": "ml",  # Malayalam
            "hin_Deva": "hi",  # Hindi
            "tam_Tamil": "ta",  # Tamil
            "tel_Telu": "te",  # Telugu
            "kan_Knda": "kn",  # Kannada
            "ben_Beng": "bn",  # Bengali
            "guj_Gujr": "gu",  # Gujarati
            "mar_Deva": "mr",  # Marathi
            "pan_Guru": "pa",  # Punjabi
            "ory_Orya": "or",  # Odia
        }
        
        target_lang = language_map.get(request.target_language, request.target_language)
        
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use NLLB-200 for Malayalam, Helsinki-NLP for others
        if target_lang == "ml":
            logger.info("Using Facebook NLLB-200-distilled-600M for Malayalam translation")
            model, tokenizer = get_nllb_model()
            
            # NLLB language codes
            src_lang = "eng_Latn"  # English
            tgt_lang = "mal_Mlym"  # Malayalam
            
            # Set source language for tokenizer
            tokenizer.src_lang = src_lang
            
            # Split text into chunks by double newlines (paragraphs) to preserve structure
            # but translate in batches for speed
            paragraphs = request.text.split('\n')
            
            # Filter out empty lines but track their positions
            non_empty_paragraphs = []
            paragraph_indices = []
            for i, p in enumerate(paragraphs):
                if p.strip():
                    non_empty_paragraphs.append(p.strip())
                    paragraph_indices.append(i)
            
            logger.info(f"Translating {len(non_empty_paragraphs)} paragraphs to Malayalam (batch mode)")
            
            # Batch translate all non-empty paragraphs at once
            if non_empty_paragraphs:
                inputs = tokenizer(
                    non_empty_paragraphs,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=128  # Shorter per-paragraph limit
                ).to(device)
                
                # Generate translations for all paragraphs in one batch
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
                        max_new_tokens=150,  # Sufficient for paragraph translation
                        num_beams=2,  # Faster with minimal quality loss
                        do_sample=False,
                        no_repeat_ngram_size=2,
                    )
                
                # Decode all translations
                translated_paragraphs = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                
                # Reconstruct with original line structure
                result_lines = [''] * len(paragraphs)
                for idx, orig_idx in enumerate(paragraph_indices):
                    result_lines[orig_idx] = translated_paragraphs[idx]
                
                translated_text = '\n'.join(result_lines)
            else:
                translated_text = request.text
            
            logger.info(f"NLLB Translation complete: {len(translated_text)} characters")
        else:
            logger.info(f"Using Helsinki-NLP model for translation to {target_lang}")
            
            # Get language-specific Helsinki model
            model, tokenizer = get_model_for_language(target_lang)
            
            # Tokenize input with increased limits for full summaries
            inputs = tokenizer(
                request.text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512  # Helsinki models work best with 512 max
            ).to(device)
            
            logger.info(f"Input tokens: {inputs['input_ids'].shape[1]}")
            
            # Generate translation with increased output length
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=5,
                    early_stopping=True,
                    no_repeat_ngram_size=3
                )
            
            # Decode translation
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"Helsinki Translation output: {len(translated_text)} characters")
        
        logger.info("Translation completed successfully")
        logger.info(f"Translated text preview: {translated_text[:100]}...")
        
        # Validate translation actually happened (check for target language characters)
        has_translation = len(translated_text) > 0 and translated_text != request.text
        if not has_translation:
            logger.warning("Translation may not have worked - output matches input")
        
        return TranslationResponse(
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
