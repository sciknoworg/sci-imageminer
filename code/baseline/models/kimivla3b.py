"""
https://huggingface.co/moonshotai/Kimi-VL-A3B-Instruct
"""

def create_model():
    """Create and return the model and processor instance."""

    from transformers import AutoModelForCausalLM, AutoProcessor

    MODEL_ID = "moonshotai/Kimi-VL-A3B-Instruct"

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )

    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)

    return model, processor


def inference(model, processor, input_image, system_prompt="You are a helpful assistant.", user_prompt="Describe this image.", max_tokens=1024):
    """Run inference on the input using the model and return the output."""

    messages = [
    {
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
        return_tensors="pt"
    )
    inputs = inputs.to(model.device)

    generated_ids = model.generate(**inputs, max_new_tokens=max_tokens)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    return output_text


def postprocess_output(text):
    """Postprocess the raw model output and return the final result."""
    return str(text).strip()
