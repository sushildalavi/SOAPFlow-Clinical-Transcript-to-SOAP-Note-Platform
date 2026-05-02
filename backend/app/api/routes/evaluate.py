from fastapi import APIRouter
from app.schemas.request import EvaluateRequest
from app.schemas.response import EvaluateResponse
from app.services.evaluator import evaluate_soap

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse, tags=["Evaluation"])
async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """
    Evaluate a generated SOAP note against an optional reference note.

    - With reference note: computes ROUGE-1, ROUGE-2, ROUGE-L, BLEU, and section-level scores.
    - Without reference note: returns heuristic completeness score.
    """
    return evaluate_soap(
        transcript=request.transcript,
        generated_note=request.generated_note,
        reference_note=request.reference_note,
    )
