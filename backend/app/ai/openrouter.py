import os
import json
import httpx
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_FALLBACK_MODELS = os.getenv("OPENROUTER_FALLBACK_MODELS", "")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_model_chain() -> list[str]:
    """Build ordered list of models to try: primary first, then fallbacks."""
    models = []
    if OPENROUTER_MODEL:
        models.append(OPENROUTER_MODEL)
    if OPENROUTER_FALLBACK_MODELS:
        for m in OPENROUTER_FALLBACK_MODELS.split(","):
            m = m.strip()
            if m and m not in models:
                models.append(m)
    return models


async def _call_openrouter(
    messages: list[dict],
    response_format: dict | None = None,
) -> dict:
    """Call OpenRouter with automatic fallback on 429 errors."""

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured")

    models = _get_model_chain()
    if not models:
        raise ValueError("No models configured. Set OPENROUTER_MODEL in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        for model in models:
            payload = {
                "model": model,
                "messages": messages,
            }
            if response_format:
                payload["response_format"] = response_format

            try:
                response = await client.post(
                    OPENROUTER_URL,
                    headers=headers,
                    json=payload,
                )

                data = response.json()

                if response.status_code == 200 and "choices" in data:
                    return {
                        "model_used": model,
                        "content": data["choices"][0]["message"]["content"],
                    }

                # Rate limited - try next model
                if response.status_code == 429:
                    last_error = f"Model {model} rate limited (429)"
                    continue

                # Other error - try next model
                last_error = f"Model {model} error {response.status_code}: {str(data)[:100]}"
                continue

            except httpx.TimeoutException:
                last_error = f"Model {model} timed out"
                continue
            except Exception as e:
                last_error = f"Model {model} failed: {str(e)[:100]}"
                continue

    raise RuntimeError(
        f"All models failed. Last error: {last_error}"
    )


def _parse_json_content(content: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks.
    
    Attempts to fix common LLM JSON issues:
    - Markdown code blocks
    - Trailing commas
    - Missing commas between properties
    - Unterminated strings
    """
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
        content = content.strip()

    # Try parsing as-is first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Fix trailing commas: ,} or ,]
    import re
    fixed = re.sub(r',\s*([}\]])', r'\1', content)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Fix missing commas between properties: "value" "key"
    fixed2 = re.sub(r'"\s*\n\s*"', '",\n"', fixed)
    try:
        return json.loads(fixed2)
    except json.JSONDecodeError:
        pass

    # Try to find the JSON object in the content
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start:end+1])
        except json.JSONDecodeError:
            pass

    # Last resort: raise with original content for debugging
    raise json.JSONDecodeError(
        f"Failed to parse LLM JSON response",
        content,
        0,
    )


async def ask_gemma(message: str) -> str:
    """Simple chat completion."""
    result = await _call_openrouter(
        messages=[{"role": "user", "content": message}],
    )
    return result["content"]


async def generate_structured(
    system_prompt: str,
    user_message: str,
    max_retries: int = 2,
) -> dict:
    """Structured JSON generation with automatic fallback and retry."""
    last_error = None

    for attempt in range(max_retries + 1):
        result = await _call_openrouter(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
        try:
            return _parse_json_content(result["content"])
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            if attempt < max_retries:
                # Add a retry instruction to the message
                user_message = (
                    f"{user_message}\n\n"
                    "IMPORTANT: Your previous response contained invalid JSON. "
                    "Please return ONLY valid JSON with no trailing commas, "
                    "no missing commas, and properly escaped strings."
                )
                continue

    raise RuntimeError(
        f"Failed to parse JSON after {max_retries + 1} attempts: {last_error}"
    )