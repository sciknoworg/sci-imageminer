#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import getpass
from pathlib import Path
from typing import Dict, List, Set, Tuple


# -----------------------------
# Dataset traversal config
# -----------------------------
SPLITS = ("train", "dev", "test")

KEY_MAP: Dict[Tuple[str, str], str] = {
    ("atomic-layer-deposition", "experimental-usecase"): "ALDexp",
    ("atomic-layer-deposition", "simulation-usecase"): "ALDsim",
    ("atomic-layer-etching", "experimental-usecase"): "ALEexp",
    ("atomic-layer-etching", "simulation-usecase"): "ALEsim",
}

MAIN_AREA_MAP: Dict[str, str] = {
    "ALDexp": "Atomic layer deposition experimental",
    "ALDsim": "Atomic layer deposition simulation",
    "ALEexp": "Atomic layer etching experimental",
    "ALEsim": "Atomic layer etching simulation",
}

# -----------------------------
# Heuristics / filters
# -----------------------------
MIN_WORDS = 5

EXACT_BLACKLIST = {
    "you may also like",
    "paper",
}

REGEX_BLACKLIST = [
    re.compile(r"^\s*(research|review)\s+article\s*\|\s*[a-z]+\s+\d{1,2}\s*,?\s*\d{4}\s*$", re.I),
    re.compile(r"^\s*published\s+on\s+web\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*$", re.I),
    re.compile(r"^\s*published\s+on\s+web\b.*$", re.I),
    re.compile(r"^\s*(?:[a-z]+\s+)?a\s*r\s*t\s*i\s*c\s*l\s*e\s*s\s*$", re.I),
    re.compile(r"^\s*article\s*\|\s*[a-z]+\s+\d{1,2}\s*,?\s*\d{4}\s*$", re.I),
]


def normalize_text(s: str) -> str:
    return " ".join(s.replace("\u00a0", " ").split()).strip()


def word_count(s: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?", s))


def is_blacklisted(s: str) -> bool:
    s_norm = normalize_text(s)
    if not s_norm:
        return True
    if s_norm.lower() in EXACT_BLACKLIST:
        return True
    return any(pat.match(s_norm) for pat in REGEX_BLACKLIST)


def pick_best_text_from_content_json(content_json_path: Path) -> str | None:
    """
    Scan content.json list-of-dicts for the first 'text' that:
      - is non-empty
      - is not blacklisted
      - has >= MIN_WORDS
    If none meet MIN_WORDS, fall back to first non-blacklisted non-empty.
    """
    try:
        with content_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, list) or not data:
        return None

    fallback: str | None = None

    for item in data:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not isinstance(text, str):
            continue

        text = normalize_text(text)
        if is_blacklisted(text):
            continue

        if fallback is None:
            fallback = text

        if word_count(text) >= MIN_WORDS:
            return text

    return fallback


def collect_texts(root: Path, verbose: bool = True) -> Dict[str, List[str]]:
    results: Dict[str, List[str]] = {k: [] for k in MAIN_AREA_MAP.keys()}
    seen: Dict[str, Set[str]] = {k: set() for k in results}

    if verbose:
        print(f"[root] {root}")

    for split in SPLITS:
        split_dir = root / split
        if not split_dir.is_dir():
            if verbose:
                print(f"[skip] missing split dir: {split_dir}")
            continue

        if verbose:
            print(f"[split] {split_dir}")

        for (domain, usecase), out_key in KEY_MAP.items():
            base = split_dir / domain / usecase
            if not base.is_dir():
                if verbose:
                    print(f"  [skip] missing: {base}")
                continue

            files = list(base.glob("*/content.json"))
            if verbose:
                print(f"  [{out_key}] found {len(files)} content.json files in {base}")

            for content_json in files:
                text = pick_best_text_from_content_json(content_json)
                if text and text not in seen[out_key]:
                    seen[out_key].add(text)
                    results[out_key].append(text)

    if verbose:
        print("[done] unique counts:", {k: len(v) for k, v in results.items()})

    return results


# -----------------------------
# LLM taxonomy generation
# -----------------------------
SYSTEM_PROMPT = """You are an expert at organizing scientific research topics.

Your task is to infer a generic taxonomy of research subareas from a list of paper titles and an overarching research field.

Guidelines:
- The taxonomy must stay within the provided main research area.
- Produce between 1 and 5 level-2 subareas (5 is a hard maximum, not a target). Use fewer when the titles do not justify more distinct generic subareas.
- Level-2 subareas must be generic, widely recognized research areas that other researchers in the field would also recognize and work in.
- The taxonomy should reflect the given paper-title collection, but treat the titles as only a small sample of the field.

Balancing generalization and evidence:
- Use the titles as evidence of topics present in the collection.
- However, do not restrict subareas only to patterns repeated across multiple titles.
- If a title clearly corresponds to a broader, well-known research area in the field, you may introduce that area even if it appears in only one title.
- Avoid creating overly specific or paper-level topics; prefer canonical research-area names.
- Merge synonyms or near-duplicate concepts into a single standard label.

Hierarchy:
- Level 1: main research area (given)
- Level 2: 1–5 major research subareas
- Level 3: optional sub-subareas that help clarify the structure of a subarea

Output format:
Return only a hierarchical list using the following indentation style:

Main Area
- Subarea
-- Sub-subarea
-- Sub-subarea
- Subarea
-- Sub-subarea

Rules:
- Use "-" for level 2
- Use "--" for level 3
- Keep labels short (2–6 words)
- Do not include numbering, explanations, or extra text"""

USER_PROMPT_TEMPLATE = """Main research area:
{{MAIN_AREA}}

Paper titles:
{{LIST_OF_TITLES}}

Generate the taxonomy.
"""


def chunk_titles(titles: List[str], max_chars: int) -> List[List[str]]:
    """
    If the title list is huge, split into chunks by approximate character budget.
    This avoids request-size blowups.
    """
    chunks: List[List[str]] = []
    cur: List[str] = []
    cur_len = 0

    for t in titles:
        line = f"- {t}\n"
        if cur and (cur_len + len(line) > max_chars):
            chunks.append(cur)
            cur = []
            cur_len = 0
        cur.append(t)
        cur_len += len(line)

    if cur:
        chunks.append(cur)

    return chunks


def build_user_prompt(main_area: str, titles: List[str]) -> str:
    # Bullet list is easiest for LLMs
    titles_block = "\n".join(f"- {t}" for t in titles)
    return (
        USER_PROMPT_TEMPLATE
        .replace("{{MAIN_AREA}}", main_area)
        .replace("{{LIST_OF_TITLES}}", titles_block)
    )


def call_llm_taxonomy(
    api_key: str,
    base_url: str,
    model: str,
    main_area: str,
    titles: List[str],
) -> str:
    """
    Calls the chat completions endpoint. If titles are very large, it:
      1) creates per-chunk mini-taxonomies
      2) asks the model to merge them into one final taxonomy
    """
    from openai import OpenAI  # requires `pip install openai`

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Rough safety: keep initial call under ~40k chars of titles.
    # Adjust if your gateway supports larger prompts.
    chunks = chunk_titles(titles, max_chars=40_000)

    if len(chunks) == 1:
        user_prompt = build_user_prompt(main_area, titles)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content.strip()

    # Multi-step: per-chunk taxonomy then merge
    partial_taxonomies: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        user_prompt = build_user_prompt(main_area, chunk)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        partial = resp.choices[0].message.content.strip()
        partial_taxonomies.append(f"### Partial taxonomy {i}\n{partial}")

    merge_system = SYSTEM_PROMPT
    merge_user = (
        f"Main research area:\n{main_area}\n\n"
        "Below are multiple partial taxonomies inferred from subsets of titles.\n"
        "Merge them into ONE clean taxonomy, removing duplicates and harmonizing labels.\n\n"
        + "\n\n".join(partial_taxonomies)
        + "\n\nReturn only the final taxonomy in the required indentation format."
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": merge_system},
            {"role": "user", "content": merge_user},
        ],
    )
    return resp.choices[0].message.content.strip()


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract title-like strings and generate LLM taxonomies for ALD/ALE exp/sim."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Dataset root containing train/dev/test (default: current directory).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress/debug prints.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Only extract titles; do not call the LLM.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("."),
        help="Directory to write taxonomy files (default: current directory).",
    )
    parser.add_argument(
        "--model",
        default="mistral-large-3-675b-instruct-2512",
        help="Model name for the AcademicCloud endpoint.",
    )
    parser.add_argument(
        "--base-url",
        default="https://chat-ai.academiccloud.de/v1",
        help="Base URL for the AcademicCloud OpenAI-compatible endpoint.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    verbose = not args.quiet

    # 1) Extract titles
    extracted = collect_texts(root, verbose=verbose)

    # Optionally persist extracted lists (useful for inspection)
    (outdir / "extracted_titles.json").write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if verbose:
        print(f"[write] {outdir / 'extracted_titles.json'}")

    if args.skip_llm:
        if verbose:
            print("[skip] LLM calls disabled (--skip-llm).")
        return

    # 2) Prompt for API key (don’t echo)
    api_key = getpass.getpass("Enter your API key (input hidden): ").strip()
    if not api_key:
        print("Error: API key is empty.", file=sys.stderr)
        sys.exit(1)

    # 3) Generate taxonomies and write one file per category
    for key in ("ALDexp", "ALDsim", "ALEexp", "ALEsim"):
        titles = extracted.get(key, [])
        main_area = MAIN_AREA_MAP[key]

        if verbose:
            print(f"[llm] Generating taxonomy for {key} ({len(titles)} titles) ...")

        if not titles:
            taxonomy = f"{main_area}\n- (no titles found)"
        else:
            taxonomy = call_llm_taxonomy(
                api_key=api_key,
                base_url=args.base_url,
                model=args.model,
                main_area=main_area,
                titles=titles,
            )

        out_path = outdir / f"{key}.txt"
        out_path.write_text(taxonomy + "\n", encoding="utf-8")

        if verbose:
            print(f"[write] {out_path}")

    if verbose:
        print("[done] All taxonomy files written.")


if __name__ == "__main__":
    main()