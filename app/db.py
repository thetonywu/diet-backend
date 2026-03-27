import os

import httpx

_supabase_url: str | None = None
_supabase_key: str | None = None


def _get_config() -> tuple[str, str]:
    global _supabase_url, _supabase_key
    if _supabase_url is None:
        _supabase_url = os.getenv("SUPABASE_URL")
        _supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not _supabase_url or not _supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return _supabase_url, _supabase_key


async def insert_chat_request(
    user_id: str,
    message: str,
    input: list[dict],
    response: str,
    matched_articles: list[dict] | None = None,
) -> None:
    url, key = _get_config()
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{url}/rest/v1/chat_requests",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "user_id": user_id,
                "message": message,
                "input": input,
                "response": response,
                "matched_articles": matched_articles,
            },
        )
