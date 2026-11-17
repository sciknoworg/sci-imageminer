"""
https://huggingface.co/OpenGVLab/InternVL3_5-8B
"""

def create_model():
    """Create and return the model and processor instance."""

    from transformers import AutoModelForImageTextToText, AutoProcessor

    MODEL_ID = "OpenGVLab/InternVL3_5-8B-HF"

    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True
        ).eval()
    
    processor = AutoProcessor.from_pretrained(MODEL_ID)    

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

    inputs = processor.apply_chat_template(messages, padding=True, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt").to(model.device)
    
    generate_ids = model.generate(**inputs, max_new_tokens=max_tokens)
    
    decoded_output = processor.decode(generate_ids[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True)

    return decoded_output


def postprocess_output(text):
    """Postprocess the raw model output and return the final result."""

    return str(text).strip()
