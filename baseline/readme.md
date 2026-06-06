# Baseline Experiments

This repository provides the baseline inference pipeline for evaluating multimodal models on the **Sci-ImageMiner** benchmark dataset. The script performs end-to-end inference across all four benchmark tasks: **Figure Classification**, **Data Extraction**, **Summarization**, and **Visual Question Answering (VQA)**.

## Prerequisites

* Python 3.10+
* Required Python dependencies installed according to each huggingface model.
* Input dataset prepared in the expected Sci-ImageMiner compatible format (see `Dataset Format` section).
* Prompt templates available under the `prompts/` directory.

## Directory Structure

```text
.
├── inference.py
├── models/
├── input_data/
├── outputs/
└── prompts/
    ├── system_prompt.txt
    ├── user_prompt_classification.txt
    ├── user_prompt_data_extraction.txt
    ├── user_prompt_summarization.txt
    └── user_prompt_vqa.txt
```

## Dataset Format

### Schema

```
{
    "sample_id": str,
    "classification": {
        "a": str,
        "b" str,
        ...
    },
    "data_extraction": {
        "a": str,
        "b" str,
        ...
    },
    "summarization": {
        "a": str,
        "b" str,
        ...
    },
    "vqa": {
        "a": list,
        "b" list,
        ...
    },
    "bbox": {
        "a": {
            "x": int,
            "y": int,
            "width": int,
            "height": int
        },
        "b": {
            "x": int,
            "y": int,
            "width": int,
            "height": int
        },
        ...
    }
}
```

### Example

```
{
  "sample_id": "atomic-layer-etching/experimental-usecase/16/fig_2",
  "classification": {
    "a": "multiple line chart",
    "b": "spectra chart"
  },
  "data_extraction": {
    "a": "```markdown\n| Temperature (°C) | Growth Rate (Å/cycle) |\n| --- | --- |\n| 200 | 0.85 |\n| 250 | 1.10 |\n```"
  },
  "summarization": {
    "a": "The figure shows the deposition rate as a function of temperature.",
    "b": "The panel illustrates film thickness variation over time."
  }
  "vqa": {
    "a": [
      {
        "question_type": "Structure-Property",
        "question": "Which materials are etched at CF4 concentrations above 10%?",
        "answer_type": "Factoid",
        "answer": "TiN and SiO2"
      }
    ],
    "b": [
      {
        "question_type": "Comparative/Trend",
        "question": "Does the etch rate increase with RF power?",
        "answer_type": "Yes/No",
        "answer": "Yes"
      }
    ]
  }
}
```

## Supported Models

| Model | Command-line Parameter |
| --- | --- |
| [google/gemma-4-E4B-it](https://huggingface.co/zai-org/GLM-4.6V-Flash) | gemma4e4b8b |
| [zai-org/GLM-4.6V-Flash](https://huggingface.co/zai-org/GLM-4.6V-Flash) | glm46vflash9b |
| [OpenGVLab/InternVL3_5-8B](https://huggingface.co/OpenGVLab/InternVL3_5-8B) | internvl358b |
| [moonshotai/Kimi-VL-A3B-Instruct](https://huggingface.co/moonshotai/Kimi-VL-A3B-Instruct) | kimivla3b |
| [allenai/Molmo2-8B](https://huggingface.co/allenai/Molmo2-8B) | molmo28b |
| [Qwen/Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) | qwen3vl8b |
| [Qwen/Qwen3-VL-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct) | qwen3vla3b30b |
| [Zyphra/ZAYA1-VL-8B](https://huggingface.co/Zyphra/ZAYA1-VL-8B) | zaya1vl8b |
| | |

## Running Baseline Inference

Execute the following command:

```bash
python inference.py \
    --model glm46vflash9b \
    --input-dir input_data \
    --prompt-path-system prompts/system_prompt.txt \
    --prompt-path-classification prompts/user_prompt_classification.txt \
    --prompt-path-data-extraction prompts/user_prompt_data_extraction.txt \
    --prompt-path-summarization prompts/user_prompt_summarization.txt \
    --prompt-path-vqa prompts/user_prompt_vqa.txt \
    --output-json-path outputs/glm46vflash9b.jsonl
```

## Command-Line Arguments

| Argument                        | Description                                                     |
| ------------------------------- | --------------------------------------------------------------- |
| `--model`                       | Name of the model used for inference.                           |
| `--input-dir`                   | Directory containing the input benchmark samples.               |
| `--prompt-path-system`          | Path to the shared system prompt.                               |
| `--prompt-path-classification`  | Prompt template for the figure classification task.             |
| `--prompt-path-data-extraction` | Prompt template for the data extraction task.                   |
| `--prompt-path-summarization`   | Prompt template for the figure summarization task.              |
| `--prompt-path-vqa`             | Prompt template for the visual question answering task.         |
| `--output-json-path`            | Destination path for storing model predictions in JSONL format. |
| `--limit-samples`               | Limit the samples for inference.                                | 
| `--log-raw-output`              | Log raw model outputs.                                          |

## Output Format

The inference results are saved as a JSON Lines (`.jsonl`) file.

## Notes

* Install and create virtual environments according to each model requirements.
* Ensure that all prompt files exist before running inference.
* The output directory will be created if it does not already exist.
* Different models can be evaluated by changing the value of the `--model` argument.
