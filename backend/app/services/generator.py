"""
SOAP generation service.
Supports: OpenAI GPT-4o, Anthropic Claude, and Demo (rule-based) modes.
"""
import json
import re
from functools import lru_cache
from time import perf_counter
from typing import Optional

from app.core.config import settings
from app.core.exceptions import GenerationError, APIKeyMissingError
from app.schemas.response import SOAPNote, GenerationMetadata
from app.services.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


_CODE_FENCE_PATTERN = re.compile(r"```(?:json)?", re.IGNORECASE)
_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
_SECTION_ALIASES = {
    "subjective": ("subjective", "S"),
    "objective": ("objective", "O"),
    "assessment": ("assessment", "A"),
    "plan": ("plan", "P"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_words(text: str) -> int:
    return len(text.split())


def _parse_json_response(raw: str) -> dict:
    """Robustly extract JSON from model output, repairing truncated tail."""
    raw = _CODE_FENCE_PATTERN.sub("", raw).strip().strip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = _JSON_OBJECT_PATTERN.search(raw)
    candidate = match.group(0) if match else raw

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    repaired = _repair_truncated_json(candidate)
    if repaired is not None:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    raise GenerationError("Model returned malformed JSON. Please try again.")


def _repair_truncated_json(text: str) -> str | None:
    """Best-effort repair for JSON cut off mid-string by max_tokens limits."""
    if not text or "{" not in text:
        return None
    if text.count('"') % 2 == 1:
        text = text + '"'
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")
    text = text.rstrip(", \n")
    text += "]" * max(open_brackets, 0)
    text += "}" * max(open_braces, 0)
    return text


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [_stringify(v) for v in value]
        return "\n".join(p for p in parts if p)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            text = _stringify(v)
            if not text:
                continue
            label = str(k).replace("_", " ").strip().capitalize()
            parts.append(f"{label}: {text}")
        return "\n".join(parts)
    return str(value).strip()


def _normalize_section(data: dict, *keys: str) -> str:
    for key in keys:
        if key in data:
            text = _stringify(data[key])
            if text:
                return text
    return "Not documented."


@lru_cache(maxsize=1)
def _get_openai_client(api_key: str):
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise GenerationError("openai package not installed. Run: pip install openai") from exc

    return AsyncOpenAI(api_key=api_key)


@lru_cache(maxsize=1)
def _get_anthropic_client(api_key: str):
    try:
        import anthropic
    except ImportError as exc:
        raise GenerationError("anthropic package not installed. Run: pip install anthropic") from exc

    return anthropic.AsyncAnthropic(api_key=api_key)


@lru_cache(maxsize=1)
def _get_httpx_client(base_url: str, timeout_s: float):
    try:
        import httpx
    except ImportError as exc:
        raise GenerationError("httpx not installed. Run: pip install httpx") from exc
    return httpx.AsyncClient(base_url=base_url, timeout=timeout_s)


# ---------------------------------------------------------------------------
# OpenAI generator
# ---------------------------------------------------------------------------

async def _generate_openai(transcript: str) -> tuple[dict, str]:
    if not settings.openai_api_key:
        raise APIKeyMissingError("OpenAI")
    try:
        client = _get_openai_client(settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        return _parse_json_response(raw), settings.openai_model
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(f"OpenAI generation failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Anthropic generator
# ---------------------------------------------------------------------------

async def _generate_anthropic(transcript: str) -> tuple[dict, str]:
    if not settings.anthropic_api_key:
        raise APIKeyMissingError("Anthropic")
    try:
        client = _get_anthropic_client(settings.anthropic_api_key)
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
            ],
        )
        raw = message.content[0].text
        return _parse_json_response(raw), settings.anthropic_model
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(f"Anthropic generation failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Groq generator (free-tier hosted, OpenAI-compatible API)
# ---------------------------------------------------------------------------

async def _generate_groq(transcript: str) -> tuple[dict, str]:
    if not settings.groq_api_key:
        raise APIKeyMissingError("Groq")
    client = _get_httpx_client(settings.groq_base_url, settings.groq_timeout_s)
    payload = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
        ],
    }
    try:
        response = await client.post(
            "/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:
        raise GenerationError(f"Groq generation failed: {exc}") from exc
    raw = body["choices"][0]["message"]["content"]
    return _parse_json_response(raw), settings.groq_model


# ---------------------------------------------------------------------------
# Ollama generator (local LLM)
# ---------------------------------------------------------------------------

async def _generate_ollama(transcript: str) -> tuple[dict, str]:
    client = _get_httpx_client(settings.ollama_base_url, settings.ollama_timeout_s)
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_ctx": 16384, "num_predict": 1024},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
        ],
    }
    try:
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        body = response.json()
    except Exception as exc:
        raise GenerationError(
            f"Ollama generation failed: {exc}. "
            f"Check that `ollama serve` is running and `{settings.ollama_model}` is pulled."
        ) from exc
    raw = (body.get("message") or {}).get("content") or ""
    return _parse_json_response(raw), settings.ollama_model


# ---------------------------------------------------------------------------
# MLX generator (local Apple Silicon — supports LoRA adapters)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_mlx(model_path: str, adapter_path: str):
    try:
        from mlx_lm import load, generate
    except ImportError as exc:
        raise GenerationError("mlx_lm not installed. Run: pip install mlx-lm") from exc

    kwargs = {}
    if adapter_path:
        kwargs["adapter_path"] = adapter_path
    model, tokenizer = load(model_path, **kwargs)
    return model, tokenizer, generate


async def _generate_mlx(transcript: str) -> tuple[dict, str]:
    import asyncio

    model, tokenizer, generate = _get_mlx(settings.mlx_model, settings.mlx_adapter_path)
    truncated = transcript
    if settings.mlx_max_transcript_chars and len(truncated) > settings.mlx_max_transcript_chars:
        truncated = truncated[: settings.mlx_max_transcript_chars] + "\n[... transcript truncated ...]"

    def _run() -> str:
        prompt = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=truncated)},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        return generate(model, tokenizer, prompt=prompt, max_tokens=settings.mlx_max_tokens, verbose=False)

    try:
        raw = await asyncio.to_thread(_run)
    except Exception as exc:
        raise GenerationError(f"MLX generation failed: {exc}") from exc

    label = settings.mlx_model
    if settings.mlx_adapter_path:
        label = f"{label}+{settings.mlx_adapter_path}"
    return _parse_json_response(raw), label


# ---------------------------------------------------------------------------
# Demo / rule-based generator
# ---------------------------------------------------------------------------

def _generate_demo(transcript: str) -> tuple[dict, str]:
    """
    Rule-based SOAP generation for demo/development purposes.
    NOT a substitute for real AI — used when no API key is configured.
    """
    lines = [l.strip() for l in transcript.split("\n") if l.strip()]
    lower_transcript = transcript.lower()

    # --- Subjective ---
    cc_keywords = ["chief complaint", "brings you in", "what's wrong", "how can i help",
                   "feeling", "pain", "hurt", "ache", "symptom", "complaint", "today"]
    hpi_keywords = ["started", "began", "since", "days", "weeks", "hours", "ago",
                    "worse", "better", "severe", "mild", "moderate", "radiates"]

    patient_lines = [l for l in lines if l.lower().startswith("patient:") or l.lower().startswith("pt:")]
    subjective_parts = []

    if patient_lines:
        subjective_parts.append(f"Patient reports: {' '.join(patient_lines[:4]).replace('Patient:', '').replace('Pt:', '').strip()}")
    else:
        subjective_parts.append("Patient reported symptoms as described in transcript.")

    # Duration/onset
    duration_match = re.search(r"(\d+\s+(?:days?|weeks?|hours?|months?))", lower_transcript)
    if duration_match:
        subjective_parts.append(f"Duration: {duration_match.group(1)}")

    # Pain scale
    pain_match = re.search(r"(\d+)\s*(?:out of|/)\s*10|pain.*?(\d+)/10", lower_transcript)
    if pain_match:
        subjective_parts.append(f"Pain severity noted as {pain_match.group(0)}.")

    subjective = " ".join(subjective_parts) if subjective_parts else "Patient's chief complaint and history as documented in transcript."

    # --- Objective ---
    vitals_keywords = ["bp", "blood pressure", "hr", "heart rate", "temp", "temperature",
                       "o2", "spo2", "weight", "bmi", "pulse", "respiratory", "rr"]
    exam_keywords = ["exam", "examination", "auscultation", "palpation", "tender",
                     "clear", "regular", "normal", "abnormal", "murmur", "wheeze"]

    objective_parts = []
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in vitals_keywords + exam_keywords):
            clean = re.sub(r"^(doctor|dr\.|physician|nurse|patient|pt):\s*", "", line, flags=re.IGNORECASE)
            if clean:
                objective_parts.append(clean)

    if objective_parts:
        objective = " ".join(objective_parts[:6])
    else:
        objective = "Vital signs and physical examination findings not explicitly stated in transcript. Clinical assessment pending formal documentation."

    # --- Assessment ---
    dx_keywords = ["diagnos", "impression", "likely", "suspect", "consistent with",
                   "rule out", "differential", "assessment", "condition", "disorder"]
    assessment_parts = []
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in dx_keywords):
            clean = re.sub(r"^(doctor|dr\.|physician|nurse):\s*", "", line, flags=re.IGNORECASE)
            if clean:
                assessment_parts.append(clean)

    if assessment_parts:
        assessment = " ".join(assessment_parts[:3])
    else:
        # Infer from patient complaints
        conditions = {
            "headache": "Headache — etiology to be determined. Differentials include tension-type headache, migraine, or secondary causes.",
            "chest pain": "Chest pain — requires further evaluation to rule out cardiac, pulmonary, or musculoskeletal etiology.",
            "cough": "Cough — likely upper respiratory tract infection or bronchitis; atypical pneumonia in differential.",
            "fever": "Fever — probable infectious etiology; further workup indicated.",
            "shortness of breath": "Dyspnea — cardiopulmonary evaluation required.",
            "back pain": "Low back pain — likely musculoskeletal; herniated disc and radiculopathy in differential.",
            "abdominal pain": "Abdominal pain — differential includes gastritis, appendicitis, or IBS pending further evaluation.",
            "fatigue": "Fatigue — evaluation for anemia, thyroid disorder, depression, or systemic illness indicated.",
        }
        assessment = "Clinical assessment to be determined based on full evaluation."
        for keyword, dx in conditions.items():
            if keyword in lower_transcript:
                assessment = dx
                break

    # --- Plan ---
    plan_keywords = ["prescri", "recommend", "follow up", "follow-up", "refer",
                     "order", "schedule", "return", "monitor", "ibuprofen", "tylenol",
                     "aspirin", "antibiot", "medication", "lab", "imaging", "x-ray", "mri"]
    plan_parts = []
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in plan_keywords):
            clean = re.sub(r"^(doctor|dr\.|physician|nurse):\s*", "", line, flags=re.IGNORECASE)
            if clean:
                plan_parts.append(clean)

    if plan_parts:
        plan = " ".join(plan_parts[:5])
    else:
        plan = (
            "1. Symptomatic management as appropriate. "
            "2. Order relevant diagnostic workup based on clinical findings. "
            "3. Patient education provided. "
            "4. Follow-up in 1-2 weeks or sooner if symptoms worsen. "
            "5. Return to ED/urgent care if acute deterioration."
        )

    return {
        "subjective": subjective,
        "objective": objective,
        "assessment": assessment,
        "plan": plan,
    }, "demo-rule-based"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def generate_soap(
    transcript: str,
    mode_override: Optional[str] = None,
) -> tuple[SOAPNote, GenerationMetadata]:
    start = perf_counter()
    mode = mode_override or settings.generation_mode

    # Auto-detect mode from available keys if mode is "demo" but keys exist
    if mode == "demo":
        if settings.openai_api_key:
            mode = "openai"
        elif settings.anthropic_api_key:
            mode = "anthropic"

    if mode == "openai":
        data, model_name = await _generate_openai(transcript)
    elif mode == "anthropic":
        data, model_name = await _generate_anthropic(transcript)
    elif mode == "ollama":
        data, model_name = await _generate_ollama(transcript)
    elif mode == "groq":
        data, model_name = await _generate_groq(transcript)
    elif mode == "mlx":
        data, model_name = await _generate_mlx(transcript)
    else:
        data, model_name = _generate_demo(transcript)
        mode = "demo"

    # Normalize keys
    soap_dict = {
        section: _normalize_section(data, *aliases)
        for section, aliases in _SECTION_ALIASES.items()
    }

    note = SOAPNote(**soap_dict)
    elapsed_ms = (perf_counter() - start) * 1000

    all_content = " ".join([note.subjective, note.objective, note.assessment, note.plan])
    sections_populated = sum(
        1 for s in [note.subjective, note.objective, note.assessment, note.plan]
        if s and s != "Not documented."
    )

    metadata = GenerationMetadata(
        model=model_name,
        mode=mode,
        transcript_word_count=_count_words(transcript),
        transcript_char_count=len(transcript),
        note_word_count=_count_words(all_content),
        processing_time_ms=round(elapsed_ms, 2),
        sections_populated=sections_populated,
    )

    return note, metadata
