"""
https://huggingface.co/google/gemma-4-E4B-it
"""

def create_model():
    """Create and return the model and processor instance."""
    from transformers import AutoModelForImageTextToText, AutoProcessor

    MODEL_ID = "google/gemma-4-E4B-it"

    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID,
        device_map="auto",
        attn_implementation="sdpa")
    
    processor = AutoProcessor.from_pretrained(
        MODEL_ID,
        padding_side="left"
    )

    return model, processor


def inference(model, processor, input_image, system_prompt="You are a helpful assistant.", user_prompt="Describe this image.", max_tokens=1024):
    """Run inference on the input using the model and return the output."""

    messages = [{
        "role": "system",
        "content": [{
            "type": "text",
            "text": system_prompt
        }]
    }, {
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
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
    ).to(model.device)

    input_len = inputs["input_ids"].shape[-1]

    output = model.generate(**inputs, max_new_tokens=50, cache_implementation="static")

    return processor.decode(output[0][input_len:], skip_special_tokens=True)


def postprocess_output(text):
    """Postprocess the raw model output and return the final result."""
    return text
