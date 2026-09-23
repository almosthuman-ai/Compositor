"""Named image models shared by settings and generation controls."""

PROVIDERS={'openai':'OpenAI-compatible API','gemini':'Google Gemini API'}
MODELS={
    'openai': [('GPT Image 1','gpt-image-1'),('GPT Image 1.5','gpt-image-1.5')],
    'gemini': [('Gemini 3 Pro Image (Nano Banana Pro)','gemini-3-pro-image'),
               ('Gemini 3.1 Flash Image (Nano Banana 2)','gemini-3.1-flash-image'),
               ('Gemini 2.5 Flash Image','gemini-2.5-flash-image')],
}

def model_label(provider,model):
    return next((label for label,value in MODELS.get(provider,[]) if value==model),model)
