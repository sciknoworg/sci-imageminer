# VQA Task Prompt

## System Prompt

```text
You are a domain expert in Atomic Layer Deposition and Etching in Material Science. 

Your task is to analyze the given scientific figure and extract the relevant information into a well-structured JSON format.

Focus on identifying the requested key data fields and ensuring the output adheres to the requested JSON structure.

Provide only the JSON output based on the extracted information. Avoid additional explanations or comments.
```

## User Prompt

```text
Analyze the given scientific figure and answer the question based on your analysis given the following information, construct a JSON object with the following fields:

**Question:**
{QUESTION_INPUT_TEXT}

**Question Type:**
{QUESTION_TYPE_INPUT_TEXT}

**Answer Type:**
{ANSWER_TYPE_INPUT_TEXT}


1.  **`answer`**: (String)

    *   Description: Well-thought and insightful answer from the given scientific figure that matches according to the given input "Answer Type".


**Input:**  

*   **Image**
    *   Description: A scientific figure image.

*   **Question**
    *   Description: A scientific comprehension and reasoning question.

*   **Question Type**
    *   Description: One of the four question categories: (i) Comparative/Trend (ii) Structure-Property (iii) Process-Oriented (iv) Application/Performance.
    *   Guidance:
		*   Comparative/Trend: Probe reasoning about experimental variables (e.g., temperature, pulse length, cycles) and their impact on outcomes (e.g., growth rate, thickness, emission intensity).
		*   Structure–Property: Evaluate ability to connect precursor structures (e.g., ligand families, rare earth types) with film properties (e.g., thermal stability, growth rates).
		*   Process-Oriented: Test the understanding of ALD/E cycles, precursor chemistry, and reaction mechanisms.
		*   Application/Performance: Assess reasoning about device-relevant outcomes (e.g., luminescence spectra, CIE color coordinates, solar cell efficiencies).

*   **Answer Type**
    *   Description: One of the four answer categories: (i) Yes/No (ii) Factoid (iii) List (iv) Paragraph.
    *   Guidance:
		*   Yes/No: Either "Yes" or "No".
		*   Factoid: A textual term (e.g., "O2 Plasma")
		*   List: A list of comma-separated values (order-insensitive) (e.g., Deposition, Etching)
		*   Paragraph: 1 or more sentences providing an explanatory descriptive answer.

  
**Output Requirements:** 

*   The output MUST be a single, valid JSON object. Do not include any explanatory text before or after the JSON.

*   If information for a field cannot be reliably determined from the image and caption, use `null` for string fields or an empty list `[]` for list fields.

*   Prioritize information directly observable from the visual elements of the scientific figure.
```