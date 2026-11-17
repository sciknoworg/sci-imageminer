import os
import argparse
import traceback
import json
import jsonlines

import base64
from io import BytesIO

import json
from pathlib import Path
from glob import glob
from pprint import pprint
from tqdm import tqdm
from PIL import Image


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--prompt-path-system", required=True)
    parser.add_argument("--prompt-path-classification", required=True)
    parser.add_argument("--prompt-path-data-extraction", required=True)
    parser.add_argument("--prompt-path-summarization", required=True)
    parser.add_argument("--prompt-path-vqa", required=True)
    parser.add_argument("--output-json-path", required=True)
    parser.add_argument("--limit-samples", required=False, default="0")
    parser.add_argument("--log-raw-output", required=False, default=False)
    
    return parser.parse_args()


def validate_exist(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory {path} does not exist.")


def validate_dir(path):
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Path {path} is not a directory.")


def validate_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Path {path} is not a file.")


def read_text_file(file_path):
    """Reads a text file and returns its content as a string."""
    with open(file_path, 'r') as f:
        content = f.read()
    return content


def crop_image_with_bbox_safe(image: Image.Image, bbox: tuple) -> Image.Image:
    """
    Crops a PIL image using a bounding box.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image")

    if len(bbox) != 4:
        raise ValueError("bbox must be a tuple of (x, y, width, height)")

    x, y, width, height = bbox

    if width <= 0 or height <= 0:
        # raise ValueError("width and height must be positive")
        width = image.width 
        height = image.height

    img_width, img_height = image.size

    # Convert to (left, upper, right, lower)
    left = max(0, x)
    upper = max(0, y)
    right = min(img_width, x + width)
    lower = min(img_height, y + height)

    # If completely outside the image
    if left >= right or upper >= lower:
        return image.crop((0, 0, 0, 0))  # empty image

    return image.crop((left, upper, right, lower))

def pil_to_base64(
    image: Image.Image,
    format: str = "PNG",
    quality: int = 95
) -> str:
    """
    Convert a PIL Image to a base64-encoded string.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image")

    buffered = BytesIO()

    # Convert mode if necessary (JPEG does not support RGBA)
    if format.upper() == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    save_kwargs = {}
    if format.upper() == "JPEG":
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True

    image.save(buffered, format=format, **save_kwargs)

    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    return img_base64

def get_json_file_paths(input_dir_path="./"):
    """Finds all JSON files in the input directory and returns a list of paths."""

    # fetch all paths
    json_files = list(Path(input_dir_path).rglob("*.json"))

    # filter out content.json and settings.json
    json_files = [str(item) for item in json_files if not (str(item).endswith("content.json") or str(item).endswith("settings.json"))]
    
    return list(set(json_files))

def read_data(input_dir_path, json_file_path):
    try:
        with open(json_file_path, 'r') as f:
            obj = json.load(f)

            obj["sample_id"] = os.path.join(input_dir_path, obj["sample_id"])

            # create image path
            image_path = str(json_file_path).replace(".json", ".jpg")

            # validate file existence
            if not os.path.exists(json_file_path):
                raise FileNotFoundError(f"JSON not found: {json_file_path}")

            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            return obj

    except Exception as e:
        print(f"Error: {e}. PATH = {json_file_path}")
        return {}


####################################
# MAIN
####################################

# def main():
if __name__ == "__main__":

    CHART_SPECIFIC_MODELS = ["deplot", "chartgemma", "chart-to-table", "unichart"]

    VALID_MODELS = [
        # -- MEDIUM -- #
        "zaya1vl8b", "gemma4e4b8b", "qwen3vl8b", "molmo28b", "internvl358b", "glm46vflash9b",

        # -- LARGE -- #
        "qwen3vla3b30b", "kimivla3b"]


    args = parse_args()

    # validate models
    MODEL_NAME = args.model.strip().lower()
    if MODEL_NAME not in VALID_MODELS:
        raise ValueError(f"Invalid model specified. Supported models: {VALID_MODELS}")

    # validate paths
    print("Validating paths...")
    validate_exist(args.input_dir)
    validate_exist(args.prompt_path_system)
    validate_exist(args.prompt_path_classification)
    validate_exist(args.prompt_path_data_extraction)
    validate_exist(args.prompt_path_summarization)
    validate_exist(args.prompt_path_vqa)

    # validate directories and files
    validate_dir(args.input_dir)
    validate_file(args.prompt_path_system)
    validate_file(args.prompt_path_classification)
    validate_file(args.prompt_path_data_extraction)
    validate_file(args.prompt_path_summarization)
    validate_file(args.prompt_path_vqa)

    OUTPUT_FILE_PATH = args.output_json_path

    # load prompts
    print("Loading prompts...")
    prompts = {}
    prompts["system_prompt"] = read_text_file(args.prompt_path_system)
    prompts["user_prompt_classification"] = read_text_file(args.prompt_path_classification)
    prompts["user_prompt_data_extraction"] = read_text_file(args.prompt_path_data_extraction)
    prompts["user_prompt_summarization"] = read_text_file(args.prompt_path_summarization)
    prompts["user_prompt_vqa"] = read_text_file(args.prompt_path_vqa)

    # log raw model outputs
    LOG_RAW_MODEL_OUTPUT = False
    if args.log_raw_output:
        try:
            LOG_RAW_MODEL_OUTPUT = bool(args.log_raw_output)
        except Exception as e:
            raise ValueError(f"Invalid value for --log_raw_output: {args.log_raw_output}. It should be a Bool. Error: {e}")

    # limit data samples (if specified)
    NUM_SAMPLES = 0
    print("args.limit_samples: ", args.limit_samples)
    if args.limit_samples:
        try:
            NUM_SAMPLES = int(args.limit_samples)
        except Exception as e:
            raise ValueError(f"Invalid value for --limit-samples: {args.limit_samples}. It should be an integer. Error: {e}")
        
    # read json file paths
    all_json_paths = get_json_file_paths(args.input_dir)
    existing_json_paths = []
    remaining_json_paths = []

    # read existing file, if it exist
    if os.path.exists(OUTPUT_FILE_PATH):
        with jsonlines.open(OUTPUT_FILE_PATH, mode='r')  as reader:
            for obj in reader:
                existing_json_paths.append(os.path.join(args.input_dir, obj["sample_id"]))
        
    # remove all elements of existing paths from all paths
    remaining_json_paths = [str(item) for item in all_json_paths if str(item) not in existing_json_paths]

    # limit data
    if NUM_SAMPLES > 0:
        remaining_json_paths = remaining_json_paths[:NUM_SAMPLES] # NOTE: Limit for testing

    # Show config
    print("-- Config --")
    print("Model: ", args.model)
    print("Input Directory: ", args.input_dir)
    print("Output JSON Path: ", args.output_json_path)
    print("Limit Samples: ", NUM_SAMPLES)
    print("Log Raw Model Output: ", LOG_RAW_MODEL_OUTPUT)
    print("All JSON paths: ", len(all_json_paths))
    print("Existing JSON paths: ", len(existing_json_paths))
    print("Remaining JSON paths: ", len(remaining_json_paths))
    print("Remaining JSON paths preview: ", remaining_json_paths[:2])
    print("-"*10)
    print()

    # Create model and processor accordingly
    model = None
    processor = None
    inference = None
    postprocess_output = None

    # ----- MEDIUM ----- #
    if MODEL_NAME == "qwen3vl8b":
        print("Loading Qwen/Qwen3-VL-8B-Instruct")
        from models.qwen3vl8b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    elif args.model == "zaya1vl8b":
        print("Loading Zyphra/ZAYA1-VL-8B")
        from models.zaya1vl8b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    elif args.model == "molmo28b":
        print("Loading allenai/Molmo2-8B")
        from models.molmo28b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    elif args.model == "internvl358b":
        print("Loading OpenGVLab/InternVL3_5-8B")
        from models.internvl358b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    elif args.model == "glm46vflash9b":
        print("Loading zai-org/GLM-4.6V-Flash")
        from models.glm46vflash9b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    elif args.model == "gemma4e4b8b":
        print("Loading google/gemma-4-E4B-it")
        from models.gemma4e4b8b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    
    # # ----- LARGE ----- #

    elif args.model == "kimivla3b":
        print("Loading moonshotai/Kimi-VL-A3B-Instruct")
        from models.kimivla3b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output

    elif args.model == "qwen3vla3b30b":
        print("Loading Qwen/Qwen3-VL-30B-A3B-Instruct")
        from models.qwen3vla3b30b import create_model, inference as model_inference, postprocess_output as model_postprocess_output
        model, processor = create_model()
        inference = model_inference
        postprocess_output = model_postprocess_output
  

    else:
        raise ValueError(f"Model {args.model} is not supported.")


    # Start inference loop
    print(">>> Starting inference loop...")
    # for ground_truth_data in tqdm(data):
    for json_file_path in tqdm(remaining_json_paths):
        try:
            ground_truth_data = read_data(input_dir_path=args.input_dir, json_file_path=json_file_path)
            sample_id = ground_truth_data['sample_id']

            # load image and JSON annotations
            image_path = f"{sample_id}.jpg"
            image_path = sample_id[:sample_id.rindex("/")] + "/images" + sample_id[sample_id.rindex("/"):] + ".jpg"
            image = Image.open(image_path)

            prediction_data = ground_truth_data.copy()
            for label,data in prediction_data.get("classification", {}).items():
                prediction_data["classification"][label] = ""
            for label,data in prediction_data.get("data_extraction", {}).items():
                prediction_data["data_extraction"][label] = ""
            for label,data in prediction_data.get("summarization", {}).items():
                prediction_data["summarization"][label] = ""
            for label,data in prediction_data.get("vqa", {}).items():
                for qa_pair in data:
                    qa_pair["answer"] = ""
            bounding_boxes = ground_truth_data.get("bbox", [])

            # crop base64 encoded images
            base64_encoded_images = {}
            pil_images = {}
            for label,data in bounding_boxes.items():
                cropped_image = crop_image_with_bbox_safe(image, (data.get("x", 0), data.get("y", 0), data.get("width", image.width), data.get("height", image.height)))
                b64_string = pil_to_base64(cropped_image, format="PNG")
                data_uri = f"data:image/png;base64,{b64_string}"

                base64_encoded_images[label] = data_uri
                pil_images[label] = cropped_image
                  
            if not MODEL_NAME in CHART_SPECIFIC_MODELS:

                # -- CLASSIFICATION
                for label,data in prediction_data.get("classification", {}).items():
                    if (label in base64_encoded_images):
                        response = inference(model=model,
                                             processor=processor,
                                             input_image=base64_encoded_images[label],
                                             system_prompt=prompts["system_prompt"],
                                             user_prompt=prompts["user_prompt_classification"])
                        
                        if LOG_RAW_MODEL_OUTPUT:
                            print("----- RESPONSE (CLS) -----")
                            print(response)
                    
                        output = postprocess_output(response)

                        prediction_data["classification"][label] = output

            # -- DATA EXTRACTION
            for label,data in prediction_data.get("data_extraction", {}).items():
                if (label in base64_encoded_images):
                    response = inference(model=model,
                                         processor=processor,
                                         input_image=base64_encoded_images[label],
                                         system_prompt=prompts["system_prompt"],
                                         user_prompt=prompts["user_prompt_data_extraction"])

                    if LOG_RAW_MODEL_OUTPUT:
                        print("----- RESPONSE (DTE) -----")
                        print(response)
                
                    output = postprocess_output(response)
                    prediction_data["data_extraction"][label] = output

            if not MODEL_NAME in CHART_SPECIFIC_MODELS:

                # -- SUMMARIZATION
                for label,data in prediction_data.get("summarization", {}).items():
                    if (label in base64_encoded_images):
                        response = inference(model=model,
                                             processor=processor, 
                                             input_image=base64_encoded_images[label],
                                             system_prompt=prompts["system_prompt"],
                                             user_prompt=prompts["user_prompt_summarization"])

                        if LOG_RAW_MODEL_OUTPUT:
                            print("----- RESPONSE (SUMM) -----")
                            print(response)
                   
                        output = postprocess_output(response)
                        prediction_data["summarization"][label] = output

            if not MODEL_NAME in CHART_SPECIFIC_MODELS:
                # -- VQA
                for label,data in prediction_data.get("vqa", {}).items():
                    if not (label in base64_encoded_images):
                        continue

                    for i in range(len(data)):
                        user_prompt_vqa = prompts["user_prompt_vqa"]
                        user_prompt_vqa = user_prompt_vqa.replace("{QUESTION_INPUT_TEXT}", data[i]["question_type"])
                        user_prompt_vqa = user_prompt_vqa.replace("{QUESTION_TYPE_INPUT_TEXT}", data[i]["question"])
                        user_prompt_vqa = user_prompt_vqa.replace("{ANSWER_TYPE_INPUT_TEXT}", data[i]["answer_type"])

                        response = inference(model=model,
                                             processor=processor, 
                                             input_image=base64_encoded_images[label],
                                             system_prompt=prompts["system_prompt"],
                                             user_prompt=user_prompt_vqa)

                        if LOG_RAW_MODEL_OUTPUT:
                            print("----- RESPONSE (VQA) -----")
                            print(response)
                    
                        output = postprocess_output(response)
                        data[i]["answer"] = output

            # Save
            with jsonlines.open(OUTPUT_FILE_PATH, mode='a') as writer:
                writer.write(prediction_data)

        except Exception as e:
            print("-"*10)
            print("Error: ", e)

            # Or if you want to capture it as a string
            stack_trace = traceback.format_exc()
            print(f"Stacktrace: {stack_trace}")
            print("-"*10)
