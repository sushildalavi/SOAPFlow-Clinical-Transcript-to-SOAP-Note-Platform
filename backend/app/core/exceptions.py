from fastapi import HTTPException, status


class TranscriptTooShortError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Transcript is too short to generate a meaningful SOAP note. Please provide more context.",
        )


class TranscriptTooLongError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Transcript exceeds maximum allowed length. Please shorten the input.",
        )


class GenerationError(HTTPException):
    def __init__(self, message: str = "Failed to generate SOAP note."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )


class APIKeyMissingError(HTTPException):
    def __init__(self, provider: str = "AI provider"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"API key for {provider} is not configured. Set the appropriate environment variable or switch to demo mode.",
        )
