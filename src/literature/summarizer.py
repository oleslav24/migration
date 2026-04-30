from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .evidence import EvidenceItem, filter_evidence


METHOD_KEYWORDS = [
    "interview",
    "survey",
    "ethnography",
    "digital ethnography",
    "content analysis",
    "discourse analysis",
    "topic modeling",
    "sentiment analysis",
    "network analysis",
    "интервью",
    "опрос",
    "этнография",
    "цифровая этнография",
    "контент-анализ",
    "дискурс-анализ",
    "тематическое моделирование",
]
LIMITATION_KEYWORDS = [
    "limitation",
    "bias",
    "representative",
    "sampling",
    "ограничение",
    "смещение",
    "репрезентативность",
    "выборка",
]
SENTENCE_RE = re.compile(r"(?<=[.!?。؟])\s+|(?<=[.!?])(?=[А-ЯA-Z])")
WORD_RE = re.compile(r"[\wА-Яа-яЁё-]+", re.UNICODE)


def summarize_task(
    task: dict,
    evidence: list[EvidenceItem],
    config,
) -> dict:
    settings = _summarization_config(config)
    max_items = int(settings.get("max_evidence_items", 20))
    filtered = filter_evidence(evidence, max_items=max_items)
    mode = str(settings.get("mode", "extractive"))
    if mode == "llm":
        return llm_summary(task, filtered, config)
    return extractive_summary(task, filtered)


def extractive_summary(task: dict, evidence: list[EvidenceItem]) -> dict:
    scored = _score_sentences(task, evidence)
    findings = [sentence for _score, sentence, _item in scored[:5]]
    concepts = _extract_concepts(task, evidence)
    methods = _keyword_hits(evidence, METHOD_KEYWORDS)
    limitations = _keyword_hits(evidence, LIMITATION_KEYWORDS)
    if not findings:
        findings = ["По локальному индексу не найдено достаточно релевантных фрагментов для содержательной выжимки."]

    return {
        "task_id": str(task.get("id", "manual_task")),
        "title": str(task.get("title", task.get("id", "Manual task"))),
        "question_ru": str(task.get("question_ru", "")),
        "question_en": str(task.get("question_en", "")),
        "summary_ru": _summary_text(findings, evidence),
        "key_findings": findings,
        "concepts": concepts,
        "methods": methods,
        "limitations": limitations,
        "relevance_for_project": _relevance_text(task, concepts, evidence),
        "evidence_used": [_evidence_dict(item) for item in evidence],
    }


def llm_summary(task: dict, evidence: list[EvidenceItem], config) -> dict:
    raise NotImplementedError("LLM summarization is not configured yet. Use mode='extractive'.")


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return []
    parts = [part.strip() for part in SENTENCE_RE.split(normalized) if part.strip()]
    return [part for part in parts if len(part) >= 20] or ([normalized] if normalized else [])


def _score_sentences(task: dict, evidence: list[EvidenceItem]) -> list[tuple[float, str, EvidenceItem]]:
    terms = _task_terms(task)
    scored: list[tuple[float, str, EvidenceItem]] = []
    for item in evidence:
        for sentence in split_sentences(item.text):
            lowered = sentence.lower()
            term_hits = sum(1 for term in terms if term and term in lowered)
            keyword_hits = sum(1 for term in task.get("keywords", []) if str(term).lower() in lowered)
            score = item.score + (0.2 * keyword_hits) + (0.1 * term_hits)
            scored.append((score, sentence, item))
    scored.sort(key=lambda row: row[0], reverse=True)
    return _dedupe_sentences(scored)


def _dedupe_sentences(scored: list[tuple[float, str, EvidenceItem]]) -> list[tuple[float, str, EvidenceItem]]:
    result: list[tuple[float, str, EvidenceItem]] = []
    seen: set[str] = set()
    for score, sentence, item in scored:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append((score, sentence, item))
    return result


def _task_terms(task: dict) -> list[str]:
    text = " ".join(str(task.get(key, "")) for key in ("question_ru", "question_en"))
    words = [word.lower() for word in WORD_RE.findall(text) if len(word) >= 5]
    return list(dict.fromkeys(words))


def _extract_concepts(task: dict, evidence: list[EvidenceItem]) -> list[str]:
    candidates = [str(value) for value in task.get("keywords", []) if str(value).strip()]
    text = " ".join(item.text.lower() for item in evidence)
    counts = Counter(candidate for candidate in candidates if candidate.lower() in text)
    if counts:
        return [item for item, _count in counts.most_common(10)]
    return candidates[:10]


def _keyword_hits(evidence: list[EvidenceItem], keywords: list[str]) -> list[str]:
    text = " ".join(item.text.lower() for item in evidence)
    return [keyword for keyword in keywords if keyword.lower() in text]


def _summary_text(findings: list[str], evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "Индекс не вернул evidence для этой задачи; содержательные выводы не формировались."
    return " ".join(
        [
            "Ниже приведена extractive-выжимка только по найденным фрагментам локального корпуса.",
            "Основные наблюдения:",
            " ".join(findings[:3]),
        ]
    )


def _relevance_text(task: dict, concepts: list[str], evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "Практическая релевантность не оценивалась, потому что evidence не найдено."
    focus = ", ".join(concepts[:5]) if concepts else "найденные фрагменты"
    return f"Для проекта это можно использовать как проверяемую подборку фрагментов по теме: {focus}."


def _evidence_dict(item: EvidenceItem) -> dict[str, Any]:
    return item.to_dict()


def _summarization_config(config) -> dict:
    if isinstance(config, dict):
        literature = config.get("literature", config)
    else:
        literature = getattr(config, "literature", {})
    return literature.get("summarization", {})
