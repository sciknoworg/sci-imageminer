<div align="center">
  <img src="assets/logo-github.png" alt="ALD/E-ImageMiner Logo" width="400"/>
</div>

## Project Overview  

**ALD/E-ImageMiner** is an annotation project on figures from **atomic layer deposition (ALD)** and **atomic layer etching (ALE)**, situated within the broader field of materials science and engineering. Within each of these categories, the data is further organized into the sub-categories **experimental-usecase** and **simulation-usecase**.  

It aims to host gold-standard annotations for chart classification, data extraction, summarization, and question answering—providing both pilot and full-phase data to support multimodal AI research in scientific image understanding.   

### 🗂️ Directory Structure  

We have compiled the dataset for annotation in this repository, structured into clearly defined categories and sub-categories.  
The layout reflects the distinction between ALD and ALE literature, as well as between experimental and simulation studies, making it easier to navigate both the pilot and full annotation phases.  


```text
data
├── train
│   ├── atomic-layer-deposition
│   │   ├── experimental-usecase
│   │   │   ├── paper #
│   │   │   │   ├── images
│   │   │   │   │   ├── figures
│   │   │   │   │   │   ├── filename 1.jpg          # (JPEG) actual figure image extracted using MinerU
│   │   │   │   │   │   ├── filename.caption.txt    # (Text) figure caption extracted from the paper.
│   │   │   │   │   │   ├── filename.class.txt      # (Text) chart visualization class/category extracted using Qwen 2.5 VL
│   │   │   │   │   │   ├── filename.data.txt       # (Text) data extracted as a markdown table using instruction-tuned Qwen 2.5 VL
│   │   │   │   │   │   └── filename.summary.txt    # (Text) summarization of chart visualization extracted using Qwen 2.5 VL
│   │   │   │   │   ├── formulas
│   │   │   │   │   │   ├── filename.jpg            # (JPEG) actual formula image extracted using MinerU
│   │   │   │   │   └── tables
│   │   │   │   │       ├── filename.jpg            # (JPEG) actual table image extracted using MinerU
│   │   │   │   ├── Author et al.pdf                # (PDF) actual PDF document
│   │   │   │   ├── content.json                    # (JSON) structured content extracted using MinerU
│   │   │   │   ├── content.md                      # (Markdown) structured content extracted using MinerU
│   │   │   │   ├── content.tei.xml                 # (TEI-XML) structured content extracted using GROBID
│   │   │   │   ├── content.txt                     # (Text) unstructured content extracted using MinerU
│   │   │   │   └── layout.json                     # (JSON) bounding box and segmentation data from MinerU
│   │   │   └── ...
│   │   └── simulation-usecase
│   │       └── ...
│   └── atomic-layer-etching
│       └── ...
└── dev/test
    ├── atomic-layer-deposition
    │   ├── experimental-usecase
    │   └── simulation-usecase
    └── atomic-layer-etching
        ├── experimental-usecase
        └── simulation-usecase
```

## 🛠️ Tools Used

- **[MinerU](https://github.com/opendatalab/MinerU)** → structured text, figures, formulas, and tables from PDFs. It is created by OpenDataLab as an open-source tool designed for data extraction from PDF documents, converting them into structured machine-readable formats like Markdown and JSON. MinerU can interpret the complex layout structure of research papers, including figures, tables, formulas, and text.
- **[Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)** → multimodal LLM applied for classification, extraction, and summarization. Specifically, we used [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct).  
  The [Prompts.md](Prompts.md) file documents the prompts used for information extraction (figure type, data, summary, and figure labels).  


### 📊 Dataset Statistics

#### Overall

| Category | Sub-category | PDFs | Figures | Formulas | Tables |
| --- | --- | --- | --- | --- | --- |
| atomic-layer-deposition | experimental-usecase | 66 | 552 | 102 | 76 |  796 |
| atomic-layer-deposition | simulation-usecase | 58 | 579 | 413 | 131 | 1181 |
| atomic-layer-etching | experimental-usecase | 47 | 461 | 116 | 28 |  652 |
| atomic-layer-etching | simulation-usecase | 32 | 346 | 165 | 55 |  598 |
| **Total** | - | **203** | **1938** | **796** | **290** |

#### Figure type classification

We have defined a taxonomy of 40 figure types including "unknown". The full taxonomy with descriptions, parent taxonomy category, and aliases is here [figure_taxonomy.tsv](https://github.com/sciknoworg/ALD-E-ImageMiner/blob/main/figure_taxonomy.tsv). The ALD/E-ImageMiner project maintains a focus only on figures of parent taxonomy category `quantitative plot`.


| Figure Type | Auto Labels | Human Labels |
| --- | --- | --- |
| 3d bar chart | 5 | 0 |
| 3d scatter plot | 23 | 0 |
| apparatus diagram | 98 | 0 |
| area chart | 6 | 0 |
| band diagram | 12 | 0 |
| bar chart | 46 | 0 |
| box plot | 4 | 0 |
| bubble chart | 1 | 0 |
| conceptual diagram | 127 | 0 |
| formula | 3 | 0 |
| grouped bar chart | 26 | 0 |
| heatmap | 89 | 0 |
| histogram | 2 | 0 |
| image panel | 526 | 0 |
| line chart | 1066 | 0 |
| line plot | 2 | 0 |
| map/geo chart | 4 | 0 |
| molecular structure diagram | 807 | 0 |
| multi-axis chart | 114 | 0 |
| multiple line chart | 44 | 0 |
| network diagram | 1 | 0 |
| periodic table map | 3 | 0 |
| pie chart | 8 | 0 |
| polar chart | 14 | 0 |
| process flow diagram | 28 | 0 |
| reaction scheme | 443 | 0 |
| scatter plot | 201 | 0 |
| spectra chart | 419 | 0 |
| stacked bar chart | 4 | 0 |
| table | 6 | 0 |
| timeline chart | 6 | 0 |
| unknown | 12 | 0 |
| **Total** | **4150** | **0** |

## 📜 License

### Annotations and Metadata
All annotations, labels, bounding boxes, and structured metadata in this repository are licensed under CC BY 4.0 (see LICENSE file).

You are free to use, modify, and redistribute the annotations with proper attribution.

### Images
Images were extracted from published scientific articles. Copyright remains with the original authors and/or publishers.

Images are provided for research purposes only. Users are responsible for complying with the licensing terms of the original publications.