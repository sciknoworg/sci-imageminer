"""
https://huggingface.co/allenai/Molmo2-8B
"""

def create_model():
    """Create and return the model and processor instance."""

    from transformers import AutoProcessor, AutoModelForImageTextToText

    model_id="allenai/Molmo2-8B"

    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True,
        dtype="auto",
        device_map="auto"
    )

    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        trust_remote_code=True,
        dtype="auto",
        device_map="auto"
    )

    return model, processor

def inference(model, processor, input_image, system_prompt="You are a helpful assistant.", user_prompt="Describe this image.", max_tokens=1024):
    """Run inference on the input using the model and return the output."""

    import torch
    
    messages = [
    # NOTE: MOLMO2-8b crashes with a system prompt and requires something like: USER/ASSISTANT/USER/ASSISTANT chats
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": input_image
            },
            {
                "type": "text",
                "text": user_prompt
            },
        ],
    }]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )

    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.inference_mode():
        generated_ids = model.generate(**inputs, max_new_tokens=max_tokens)

    generated_tokens = generated_ids[0, inputs['input_ids'].size(1):]
    generated_text = processor.tokenizer.decode(generated_tokens, skip_special_tokens=True)

    return generated_text


def postprocess_output(text):
    """Postprocess the raw model output and return the final result."""
    return str(text).strip()
