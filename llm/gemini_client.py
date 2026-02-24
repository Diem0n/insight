import time
from google import genai
from google.genai import errors as genai_errors
import config

_client = genai.Client(api_key=config.GEMINI_API_KEY)

_RETRY_DELAYS = (10, 30, 60)


def generate(prompt: str) -> str:
    last_exc = None
    for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
        try:
            response = _client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except genai_errors.ClientError as exc:
            if exc.status_code == 429 and delay is not None:
                last_exc = exc
                time.sleep(delay)
                continue
            raise
    raise last_exc
