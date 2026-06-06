"""
https://huggingface.co/Zyphra/ZAYA1-VL-8B
"""

def create_model():
    """Create and return the model and processor instance."""
    # import torch
    from transformers import Zaya1VLForConditionalGeneration, Zaya1VLProcessor
    
    # device = "cuda"
    processor = Zaya1VLProcessor.from_pretrained("Zyphra/ZAYA1-VL-8B",
                                                 temporal_patch_size=1)
    model = Zaya1VLForConditionalGeneration.from_pretrained("Zyphra/ZAYA1-VL-8B",
                                                            # device_map=device,
                                                            # torch_dtype=torch.bfloat16,
                                                            device_map="auto",
                                                            dtype="auto",
                                                            # attn_implementation="flash_attention_2"
                                                            )

    return model, processor


def inference(model, processor, input_image, system_prompt="You are a helpful assistant.", user_prompt="Describe this image.", max_tokens=1024):
    """Run inference on the input using the model and return the output."""

    # from PIL import Image
    from qwen_vl_utils import process_vision_info
    # import requests

    device = "cuda"
    # image = Image.open(requests.get(input_image, stream=True).raw)
    num_img_tokens = 8000

    conversation = [{
            "role": "system",
            "content": [{
                "type": "text",
                "text": system_prompt
            }]
        }, {
        "role": "user",
        "content": [{
            "type": "image",
            # "image": image,
            "image": input_image,
            "max_pixels" : num_img_tokens * 28 * 28,
            "min_pixels" : 10 * 28 * 28
        },
        {
            "type": "text",
            "text": user_prompt
        }]
    }]

    prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
    images, _ = process_vision_info(conversation)
    inputs = processor(text=prompt, images=images, add_special_tokens=True, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    outputs = model.generate(**inputs, max_new_tokens=max_tokens)
    output_text = processor.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])

    return output_text


def postprocess_output(text):
    """Postprocess the raw model output and return the final result."""

    # from utils.json_llm_response import llm_response_to_json
    # return llm_response_to_json(text)

    if text:
        return str(text).replace("<|im_end|>", "").strip()
    else:
        return ""


def cleanup(model):
    """Clean up any resources used by the model."""
    pass