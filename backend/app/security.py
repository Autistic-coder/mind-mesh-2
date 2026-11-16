from __future__ import annotations

import hashlib
import secrets
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import SessionRecord, User

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
_attempts: dict[str, deque[float]] = defaultdict(deque)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def new_session(db: Session, user: User) -> tuple[SessionRecord, str]:
    raw = secrets.token_urlsafe(32)
    record = SessionRecord(
        id=hashlib.sha256(raw.encode()).hexdigest(),
        user_id=user.id,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=datetime.now(UTC) + timedelta(days=settings.session_days),
    )
    db.add(record)
    db.commit()
    return record, raw


def session_from_request(request: Request, db: Session) -> SessionRecord | None:
    raw = request.cookies.get("mindmesh_session")
    if not raw:
        return None
    record = db.get(SessionRecord, hashlib.sha256(raw.encode()).hexdigest())
    if not record:
        return None
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        db.delete(record)
        db.commit()
        return None
    return record


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    record = session_from_request(request, db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    user = db.get(User, record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return user


def require_csrf(request: Request, db: Session = Depends(get_db)) -> None:
    record = session_from_request(request, db)
    supplied = request.headers.get("X-CSRF-Token", "")
    if not record or not supplied or not secrets.compare_digest(record.csrf_token, supplied):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def rate_limit(request: Request, scope: str, limit: int, window: int) -> None:
    key = f"{scope}:{request.client.host if request.client else 'unknown'}"
    now = time.monotonic()
    bucket = _attempts[key]
    while bucket and bucket[0] <= now - window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests; please try again later")
    bucket.append(now)


def clear_rate_limits() -> None:
    _attempts.clear()
