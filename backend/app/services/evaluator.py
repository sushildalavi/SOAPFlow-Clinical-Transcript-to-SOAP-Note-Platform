"""
Evaluation service for SOAP note quality metrics.
Supports ROUGE, BLEU, and section-level scoring when reference notes are provided.
"""
from functools import lru_cache
from typing import Optional
from app.schemas.response import EvaluationScores, EvaluateResponse


@lru_cache(maxsize=1)
def _get_rouge_scorer():
    from rouge_score import rouge_scorer

    return rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)


def _safe_rouge(hypothesis: str, reference: str) -> dict:
    """Compute ROUGE scores, returning zeros if rouge_score not installed."""
    if not hypothesis.strip() or not reference.strip():
        return {"rouge_1": None, "rouge_2": None, "rouge_l": None}

    try:
        scores = _get_rouge_scorer().score(reference, hypothesis)
        return {
            "rouge_1": round(scores["rouge1"].fmeasure, 4),
            "rouge_2": round(scores["rouge2"].fmeasure, 4),
            "rouge_l": round(scores["rougeL"].fmeasure, 4),
        }
    except ImportError:
        return {"rouge_1": None, "rouge_2": None, "rouge_l": None}


def _safe_bleu(hypothesis: str, reference: str) -> Optional[float]:
    """Compute corpus BLEU, returning None if nltk not installed."""
    if not hypothesis.strip() or not reference.strip():
        return None

    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        ref_tokens = reference.lower().split()
        hyp_tokens = hypothesis.lower().split()
        score = sentence_bleu(
            [ref_tokens],
            hyp_tokens,
            smoothing_function=SmoothingFunction().method1,
        )
        return round(score, 4)
    except ImportError:
        return None


def _heuristic_score(note: dict) -> float:
    """
    Lightweight heuristic quality score (0–1) when no reference is available.
    Based on section completeness and length adequacy.
    """
    sections = ["subjective", "objective", "assessment", "plan"]
    total_score = 0.0

    for section in sections:
        content = note.get(section, "")
        if not content or content.strip() in {"Not documented.", "N/A", ""}:
            continue
        words = len(content.split())
        # Score based on word count: target 20+ words per section
        section_score = min(1.0, words / 20)
        total_score += section_score

    return round(total_score / len(sections), 4)


def evaluate_soap(
    transcript: str,
    generated_note: dict,
    reference_note: Optional[dict] = None,
) -> EvaluateResponse:
    if reference_note:
        # Full evaluation against reference
        gen_text = " ".join(generated_note.get(k, "") for k in ["subjective", "objective", "assessment", "plan"])
        ref_text = " ".join(reference_note.get(k, "") for k in ["subjective", "objective", "assessment", "plan"])

        rouge_scores = _safe_rouge(gen_text, ref_text)
        bleu = _safe_bleu(gen_text, ref_text)

        # Section-level ROUGE-L
        section_scores = {}
        for section in ["subjective", "objective", "assessment", "plan"]:
            gen_sec = generated_note.get(section, "")
            ref_sec = reference_note.get(section, "")
            if gen_sec and ref_sec:
                sec_rouge = _safe_rouge(gen_sec, ref_sec)
                rouge_l = sec_rouge.get("rouge_l")
                if rouge_l is not None:
                    section_scores[section] = rouge_l

        scores = EvaluationScores(
            rouge_1=rouge_scores.get("rouge_1"),
            rouge_2=rouge_scores.get("rouge_2"),
            rouge_l=rouge_scores.get("rouge_l"),
            bleu=bleu,
            section_scores=section_scores if section_scores else None,
        )

        rouge_l = scores.rouge_l or 0.0
        quality_label = "Excellent" if rouge_l > 0.7 else "Good" if rouge_l > 0.4 else "Fair" if rouge_l > 0.2 else "Needs Review"
        summary = (
            f"Evaluation against reference note: ROUGE-L={rouge_l:.3f} ({quality_label}). "
            f"ROUGE-1={scores.rouge_1 or 'N/A'}, ROUGE-2={scores.rouge_2 or 'N/A'}, "
            f"BLEU={scores.bleu or 'N/A'}."
        )
    else:
        # Heuristic-only evaluation
        heuristic = _heuristic_score(generated_note)
        quality_label = "Excellent" if heuristic > 0.8 else "Good" if heuristic > 0.6 else "Fair" if heuristic > 0.4 else "Needs Review"
        scores = EvaluationScores(
            section_scores={"heuristic_completeness": heuristic},
        )
        summary = (
            f"No reference note provided. Heuristic completeness score: {heuristic:.2f} ({quality_label}). "
            f"For full ROUGE/BLEU evaluation, provide a reference note."
        )

    return EvaluateResponse(success=True, scores=scores, summary=summary)
