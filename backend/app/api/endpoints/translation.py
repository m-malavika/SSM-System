"""
Translation endpoint using CTranslate2 INT8 quantized NLLB-200 for Malayalam (5-10x faster)
and Helsinki-NLP for other Indian languages
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_user
from app.models.user import User
import logging
import time
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Global cache for CTranslate2 models
_ct2_translator = None
_ct2_tokenizer = None
_translation_model = None
_tokenizer = None
_device = None

# Path for converted CTranslate2 model
CT2_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "nllb-200-distilled-600M-int8")

@router.post("/clear-translation-cache")
async def clear_translation_cache(current_user: User = Depends(get_current_user)):
    """Force clear translation models cache - requires restart to take effect"""
    global _ct2_translator, _ct2_tokenizer, _translation_model, _tokenizer, _device
    
    old_type = "CTranslate2" if _ct2_translator else ("Helsinki" if _translation_model else "None")
    
    _ct2_translator = None
    _ct2_tokenizer = None
    _translation_model = None
    _tokenizer = None
    _device = None
    
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


def _convert_nllb_to_ct2():
    """Convert NLLB model to CTranslate2 INT8 format (one-time operation)"""
    import ctranslate2
    
    logger.info("Converting NLLB-200-distilled-600M to CTranslate2 INT8 format...")
    logger.info("This is a one-time operation and will take a few minutes...")
    
    start_time = time.time()
    
    # Create models directory if it doesn't exist
    os.makedirs(os.path.dirname(CT2_MODEL_PATH), exist_ok=True)
    
    # Convert using ctranslate2 converter
    ctranslate2.converters.TransformersConverter(
        "facebook/nllb-200-distilled-600M"
    ).convert(
        CT2_MODEL_PATH,
        quantization="int8",  # INT8 quantization for 4x speed + smaller size
        force=True
    )
    
    elapsed = time.time() - start_time
    logger.info(f"✓ Model converted to CTranslate2 INT8 in {elapsed:.1f}s")
    logger.info(f"  Saved to: {CT2_MODEL_PATH}")


def get_ct2_nllb_model():
    """
    Load CTranslate2 INT8 quantized NLLB model for Malayalam translation
    MAXIMUM SPEED: Optimized for fastest possible inference
    """
    global _ct2_translator, _ct2_tokenizer, _device
    
    if _ct2_translator is None:
        import ctranslate2
        from transformers import NllbTokenizerFast
        import torch
        import multiprocessing
        
        start_time = time.time()
        
        # Check if converted model exists, if not convert it
        if not os.path.exists(CT2_MODEL_PATH):
            _convert_nllb_to_ct2()
        
        # Determine device
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Get optimal thread count
        cpu_count = multiprocessing.cpu_count()
        
        logger.info(f"Loading CTranslate2 INT8 NLLB model on {_device} with {cpu_count} threads...")
        
        # MAXIMUM SPEED settings
        _ct2_translator = ctranslate2.Translator(
            CT2_MODEL_PATH,
            device=_device,
            compute_type="int8",
            inter_threads=cpu_count,
            intra_threads=2,  # Some intra-op parallelism helps
        )
        
        # Use FAST tokenizer (2-5x faster tokenization)
        _ct2_tokenizer = NllbTokenizerFast.from_pretrained(
            "facebook/nllb-200-distilled-600M",
            use_fast=True
        )
        
        # Warm up the model (first inference is slow)
        logger.info("Warming up model...")
        _ct2_tokenizer.src_lang = "eng_Latn"
        warmup_tokens = _ct2_tokenizer("Hello", return_tensors=None)["input_ids"]
        warmup_tokens = _ct2_tokenizer.convert_ids_to_tokens(warmup_tokens)
        _ct2_translator.translate_batch([warmup_tokens], target_prefix=[["mal_Mlym"]], beam_size=1)
        
        load_time = time.time() - start_time
        logger.info(f"✓ CTranslate2 INT8 NLLB model loaded and warmed up in {load_time:.1f}s")
    
    return _ct2_translator, _ct2_tokenizer, _device


def get_model_for_language(target_lang):
    """Get or load the appropriate model for the target language (non-Malayalam)
    OPTIMIZED: Uses half-precision on GPU and eval mode
    """
    from transformers import MarianMTModel, MarianTokenizer
    import torch
    
    global _translation_model, _tokenizer, _device
    
    if _translation_model is None:
        _translation_model = {}
        _tokenizer = {}
    
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    
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
        
        use_half = _device == "cuda"
        if use_half:
            _translation_model[target_lang] = MarianMTModel.from_pretrained(
                model_name,
                torch_dtype=torch.float16
            ).to(_device)
        else:
            _translation_model[target_lang] = MarianMTModel.from_pretrained(model_name).to(_device)
        
        _translation_model[target_lang].eval()
        logger.info(f"Model for {target_lang} loaded on {_device} (half={use_half})")
    
    return _translation_model[target_lang], _tokenizer[target_lang], _device

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Translate text from English to Indian languages
    ULTRA-FAST: Uses CTranslate2 INT8 quantized NLLB-200 (5-10x faster than PyTorch)
    
    Supported language codes:
    - mal_Mlym: Malayalam (ml) - Uses CTranslate2 INT8 NLLB-200
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
        start_time = time.time()
        logger.info(f"Translation request from user {current_user.username} to {request.target_language}")
        logger.info(f"Text length: {len(request.text)} characters")
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Validate text length (AI summaries are typically 100-2000 chars)
        if len(request.text) > 5000:
            logger.warning(f"Large text received: {len(request.text)} chars")
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
        
        # Use CTranslate2 INT8 NLLB for Malayalam, Helsinki-NLP for others
        if target_lang == "ml":
            logger.info("Using CTranslate2 INT8 NLLB-200 for Malayalam (ultra-fast)")
            translator, tokenizer, device = get_ct2_nllb_model()
            
            # NLLB language codes
            src_lang = "eng_Latn"
            tgt_lang = "mal_Mlym"
            
            # Set source language for tokenizer
            tokenizer.src_lang = src_lang
            
            text_to_translate = request.text.strip()
            
            # MAXIMUM SPEED: Merge into larger chunks (fewer translations = faster)
            # Split by double newlines (paragraphs) to preserve major structure
            paragraphs = text_to_translate.split('\n\n')
            
            if not paragraphs or (len(paragraphs) == 1 and not paragraphs[0].strip()):
                translated_text = ""
            else:
                # Filter and prepare paragraphs
                para_map = []  # (index, content) for non-empty paragraphs
                for i, para in enumerate(paragraphs):
                    stripped = para.strip()
                    if stripped:
                        # Replace internal newlines with space to make single chunk
                        merged = ' '.join(stripped.split('\n'))
                        para_map.append((i, merged))
                
                if not para_map:
                    translated_text = ""
                else:
                    logger.info(f"Translating {len(para_map)} paragraphs (merged for speed)")
                    
                    # FAST batch tokenization using list comprehension
                    all_source_tokens = [
                        tokenizer.convert_ids_to_tokens(
                            tokenizer(content, return_tensors=None, add_special_tokens=True)["input_ids"]
                        )
                        for _, content in para_map
                    ]
                    
                    # Single optimized batch call
                    results = translator.translate_batch(
                        all_source_tokens,
                        target_prefix=[[tgt_lang]] * len(para_map),
                        beam_size=1,  # Greedy = fastest
                        max_decoding_length=400,
                        replace_unknowns=True,
                        max_batch_size=0,  # 0 = no limit, process all at once
                        batch_type="tokens",  # Batch by tokens for better GPU/CPU utilization
                    )
                    
                    # Fast batch decode using list comprehension
                    translated_paras = [
                        tokenizer.decode(
                            tokenizer.convert_tokens_to_ids(
                                r.hypotheses[0][1:] if r.hypotheses[0] and r.hypotheses[0][0] == tgt_lang else r.hypotheses[0]
                            ),
                            skip_special_tokens=True
                        )
                        for r in results
                    ]
                    
                    # Reconstruct with paragraph structure
                    result_paras = [''] * len(paragraphs)
                    for idx, (orig_idx, _) in enumerate(para_map):
                        result_paras[orig_idx] = translated_paras[idx]
                    
                    translated_text = '\n\n'.join(result_paras)
            
            elapsed = time.time() - start_time
            logger.info(f"CTranslate2 INT8 Translation complete: {len(translated_text)} chars in {elapsed:.2f}s")
        else:
            logger.info(f"Using Helsinki-NLP model for translation to {target_lang}")
            import torch
            
            # Get language-specific Helsinki model
            model, tokenizer, device = get_model_for_language(target_lang)
            
            # Tokenize input
            inputs = tokenizer(
                request.text,
                return_tensors="pt",
                padding=False,
                truncation=True,
                max_length=512
            ).to(device)
            
            logger.info(f"Input tokens: {inputs['input_ids'].shape[1]}")
            
            # OPTIMIZED: Use greedy decoding for speed
            with torch.no_grad(), torch.cuda.amp.autocast(enabled=(device == "cuda")):
                outputs = model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=1,  # Greedy decoding - much faster
                    do_sample=False,
                    use_cache=True,
                )
            
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            elapsed = time.time() - start_time
            logger.info(f"Helsinki Translation complete: {len(translated_text)} chars in {elapsed:.2f}s")
        
        logger.info(f"Translation completed successfully in {time.time() - start_time:.2f}s")
        logger.info(f"Translated text preview: {translated_text[:100]}...")
        
        # Validate translation actually happened
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
