"""
https://huggingface.co/zai-org/GLM-4.6V-Flash
"""


def create_model():
    """Create and return the model and processor instance."""
    from transformers import AutoProcessor, Glm46VForConditionalGeneration

    MODEL_PATH = "zai-org/GLM-4.6V-Flash"

    processor = AutoProcessor.from_pretrained(MODEL_PATH)
    
    model = Glm46VForConditionalGeneration.from_pretrained(
        pretrained_model_name_or_path=MODEL_PATH,
        torch_dtype="auto",
        device_map="auto",
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
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt").to(model.device)

    inputs.pop("token_type_ids", None)
    generated_ids = model.generate(**inputs, max_new_tokens=max_tokens)
    output_text = processor.decode(generated_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)

    return output_text

def postprocess_output(text):
    """Postprocess the raw model output and return the final result."""
    import re
    
    m = re.search(r"</think>\s*<\|begin_of_box\|>\s*(.*?)\s*<|end_of_box|>\s*<\|user\|>", text, re.DOTALL)
    if m:
        return  m.group(1).strip()
    else:
        m = re.search(r"</think>\s*(.*?)\s*<\|user\|>", text, re.DOTALL)
        if m:
            return  m.group(1).strip()
        else:
            return ""
