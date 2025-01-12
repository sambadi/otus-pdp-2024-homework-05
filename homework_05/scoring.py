import hashlib
import json
from datetime import datetime
from typing import Optional

from homework_05.store import Store


def get_scoring_key(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    birthday: Optional[datetime] = None,
) -> str:
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        birthday.strftime("%Y%m%d") if birthday else "",
    ]
    return "uid:" + hashlib.md5("".join(key_parts).encode("utf-8")).hexdigest()


def get_score(
    store: Store,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    birthday: Optional[datetime] = None,
    gender: Optional[int] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> float:
    key = get_scoring_key(first_name, last_name, phone, birthday)

    # Try to get from cache
    score = store.cache_get(key)
    if score is not None:
        return float(score)

    # Calculate score
    score = 0.0
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender is not None:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    # Cache the score for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def get_interests(store: Store, cid: str) -> list:
    r = store.get(f"i:{cid}")
    return json.loads(r) if r else []
