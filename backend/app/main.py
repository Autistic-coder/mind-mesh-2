from __future__ import annotations

import csv
import io
import json
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .model_service import FEATURES, model_service
from .models import BatchJob, Conversation, Prediction, User
from .schemas import (
    ChatRequest,
    LoginRequest,
    MachineInput,
    PredictionResponse,
    ProfileUpdate,
    RegisterRequest,
    UserResponse,
)
from .security import (
    current_user,
    hash_password,
    new_session,
    rate_limit,
    require_csrf,
    session_from_request,
    verify_password,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    model_service.load()
    yield


app = FastAPI(title="MindMesh 2 API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


def set_session_cookies(response: Response, raw: str, csrf: str) -> None:
    common = {"secure": settings.secure_cookies, "samesite": "lax", "path": "/"}
    response.set_cookie("mindmesh_session", raw, httponly=True, max_age=604800, **common)
    response.set_cookie("mindmesh_csrf", csrf, httponly=False, max_age=604800, **common)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(503, "Database unavailable") from exc
    if not model_service.ready:
        raise HTTPException(503, model_service.error or "Model unavailable")
    return {"status": "ready", "model_version": model_service.manifest["model_version"]}


@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register(
    payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)
):
    rate_limit(request, "register", 5, 60)
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    session, raw = new_session(db, user)
    set_session_cookies(response, raw, session.csrf_token)
    return user


@app.post("/api/auth/login", response_model=UserResponse)
def login(
    payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)
):
    rate_limit(request, "login", 8, 60)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(user.password_hash, payload.password):
        raise HTTPException(401, "Invalid email or password")
    session, raw = new_session(db, user)
    set_session_cookies(response, raw, session.csrf_token)
    return user


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return user


@app.post("/api/auth/logout", status_code=204, dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    record = session_from_request(request, db)
    if record:
        db.delete(record)
        db.commit()
    response.delete_cookie("mindmesh_session", path="/")
    response.delete_cookie("mindmesh_csrf", path="/")


def serialize_prediction(item: Prediction) -> dict:
    result = "Failure Risk" if item.predicted_failure else "Normal Operation"
    recommendation = (
        "Prioritize a qualified inspection and review recent operating trends."
        if item.predicted_failure
        else "Continue routine monitoring; this result does not replace physical inspection."
    )
    return {
        "id": item.id,
        "probability": item.probability,
        "predicted_failure": item.predicted_failure,
        "result": result,
        "risk_level": item.risk_level,
        "recommendation": recommendation,
        "model_version": item.model_version,
        "created_at": item.created_at,
        "inputs": item.inputs,
    }


@app.post(
    "/api/predictions", response_model=PredictionResponse, dependencies=[Depends(require_csrf)]
)
def predict(
    payload: MachineInput,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    rate_limit(request, f"predict:{user.id}", 30, 60)
    try:
        result = model_service.predict_many([payload])[0]
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    item = Prediction(
        user_id=user.id,
        inputs=payload.feature_dict(),
        model_version=model_service.manifest["model_version"],
        **{k: result[k] for k in ("probability", "predicted_failure", "risk_level")},
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_prediction(item)


@app.get("/api/predictions")
def predictions(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    risk: str = "",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    page, page_size = max(1, page), min(100, max(1, page_size))
    query = select(Prediction).where(Prediction.user_id == user.id)
    if risk in {"low", "medium", "high"}:
        query = query.where(Prediction.risk_level == risk)
    items = db.scalars(
        query.order_by(Prediction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    if search:
        lowered = search.lower()
        items = [
            item
            for item in items
            if lowered in item.id.lower() or lowered in json.dumps(item.inputs).lower()
        ]
    total = (
        db.scalar(select(func.count()).select_from(Prediction).where(Prediction.user_id == user.id))
        or 0
    )
    return {
        "items": [serialize_prediction(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/predictions/{prediction_id}", response_model=PredictionResponse)
def prediction_detail(
    prediction_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    item = db.scalar(
        select(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == user.id)
    )
    if not item:
        raise HTTPException(404, "Prediction not found")
    return serialize_prediction(item)


@app.delete(
    "/api/predictions/{prediction_id}", status_code=204, dependencies=[Depends(require_csrf)]
)
def delete_prediction(
    prediction_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    item = db.scalar(
        select(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == user.id)
    )
    if not item:
        raise HTTPException(404, "Prediction not found")
    db.delete(item)
    db.commit()


def csv_safe(value: object) -> str:
    text_value = str(value)
    return (
        "'" + text_value if text_value.startswith(("=", "+", "-", "@", "\t", "\r")) else text_value
    )


@app.get("/api/batches/template")
def batch_template(_: User = Depends(current_user)):
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(FEATURES)
    writer.writerow(["L", 298.1, 308.6, 1551, 42.8, 0])
    return Response(
        stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mindmesh_batch_template.csv"},
    )


@app.post("/api/batches", dependencies=[Depends(require_csrf)])
async def batch_predict(
    file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a CSV file")
    raw = await file.read(1_000_001)
    if len(raw) > 1_000_000:
        raise HTTPException(413, "CSV exceeds the 1 MB limit")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if reader.fieldnames != FEATURES:
            raise HTTPException(
                422,
                {"message": "CSV columns must exactly match the template", "required": FEATURES},
            )
        source_rows = list(reader)
    except UnicodeDecodeError as exc:
        raise HTTPException(422, "CSV must be UTF-8 encoded") from exc
    if not source_rows or len(source_rows) > settings.max_batch_rows:
        raise HTTPException(422, f"CSV must contain 1 to {settings.max_batch_rows} data rows")
    valid, errors = [], []
    for number, row in enumerate(source_rows, start=2):
        try:
            valid.append(MachineInput.model_validate(row))
        except Exception as exc:
            errors.append({"row": number, "error": str(exc).splitlines()[0]})
    if errors:
        raise HTTPException(422, {"message": "Some rows are invalid", "errors": errors[:50]})
    results = model_service.predict_many(valid)
    job = BatchJob(user_id=user.id, filename=file.filename[:255], row_count=len(valid))
    db.add(job)
    db.flush()
    items = []
    for machine, result in zip(valid, results, strict=True):
        item = Prediction(
            user_id=user.id,
            batch_id=job.id,
            inputs=machine.feature_dict(),
            model_version=model_service.manifest["model_version"],
            **{k: result[k] for k in ("probability", "predicted_failure", "risk_level")},
        )
        db.add(item)
        items.append(item)
    db.commit()
    return {
        "id": job.id,
        "row_count": len(items),
        "flagged": sum(item.predicted_failure for item in items),
        "results": [serialize_prediction(item) for item in items],
    }


@app.get("/api/batches/{batch_id}/download")
def batch_download(
    batch_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    job = db.scalar(select(BatchJob).where(BatchJob.id == batch_id, BatchJob.user_id == user.id))
    if not job:
        raise HTTPException(404, "Batch not found")
    items = db.scalars(
        select(Prediction).where(Prediction.batch_id == job.id, Prediction.user_id == user.id)
    ).all()
    stream = io.StringIO()
    fields = FEATURES + ["Failure probability", "Risk level", "Result", "Model version"]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for item in items:
        row = {key: csv_safe(value) for key, value in item.inputs.items()}
        row.update(
            {
                "Failure probability": item.probability,
                "Risk level": item.risk_level,
                "Result": "Failure Risk" if item.predicted_failure else "Normal Operation",
                "Model version": item.model_version,
            }
        )
        writer.writerow(row)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mindmesh-{batch_id}.csv"},
    )


@app.get("/api/model-report")
def model_report(_: User = Depends(current_user)):
    if not model_service.manifest:
        raise HTTPException(503, "Model report unavailable")
    return model_service.manifest


@app.post("/api/conversations", dependencies=[Depends(require_csrf)])
def ask(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    rate_limit(request, f"ask:{user.id}", 10, 60)
    shared = None
    if payload.share_prediction:
        item = db.scalar(
            select(Prediction).where(
                Prediction.id == payload.prediction_id, Prediction.user_id == user.id
            )
        )
        if not item:
            raise HTTPException(404, "Prediction not found")
        shared = {
            "probability": item.probability,
            "risk_level": item.risk_level,
            "inputs": item.inputs,
        }
    user_message = Conversation(
        user_id=user.id, role="user", content=payload.message, shared_prediction=shared
    )
    db.add(user_message)
    if not settings.openai_api_key:
        reply = "Static help: MindMesh estimates failure risk from six operating readings. A flagged result should trigger qualified inspection; it does not prove a fault or replace maintenance procedures."
        mode = "static"
    else:
        context = (
            f"\nThe user explicitly shared this prediction summary: {json.dumps(shared)}"
            if shared
            else ""
        )
        try:
            with httpx.Client(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
                provider = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.openai_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are MindMesh, a concise predictive-maintenance explainer. "
                                    "Explain inputs, metrics, predictions, and terminology. Never claim "
                                    "to retrain the model, diagnose a fault, or perform maintenance. "
                                    "Remind users that model output supports, but never replaces, inspection."
                                ),
                            },
                            {"role": "user", "content": payload.message + context},
                        ],
                        "max_tokens": 500,
                    },
                )
                provider.raise_for_status()
                reply = provider.json()["choices"][0]["message"]["content"].strip()
                if not reply:
                    raise ValueError("Empty assistant response")
            mode = "ai"
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise HTTPException(
                502, "Assistant is temporarily unavailable; static model guidance remains available"
            ) from exc
    db.add(Conversation(user_id=user.id, role="assistant", content=reply))
    db.commit()
    return {"reply": reply, "mode": mode}


@app.get("/api/conversations")
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at)
    ).all()
    return [
        {"id": item.id, "role": item.role, "content": item.content, "created_at": item.created_at}
        for item in items
    ]


@app.patch("/api/account", response_model=UserResponse, dependencies=[Depends(require_csrf)])
def update_account(
    payload: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    user.display_name = payload.display_name.strip()
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/overview")
def overview(user: User = Depends(current_user), db: Session = Depends(get_db)):
    total = (
        db.scalar(select(func.count()).select_from(Prediction).where(Prediction.user_id == user.id))
        or 0
    )
    flagged = (
        db.scalar(
            select(func.count())
            .select_from(Prediction)
            .where(Prediction.user_id == user.id, Prediction.predicted_failure.is_(True))
        )
        or 0
    )
    recent = db.scalars(
        select(Prediction)
        .where(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .limit(5)
    ).all()
    return {
        "total": total,
        "flagged": flagged,
        "normal": total - flagged,
        "model_version": model_service.manifest.get("model_version"),
        "recent": [serialize_prediction(item) for item in recent],
    }


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return Response(
        content=json.dumps({"detail": "An unexpected server error occurred"}),
        status_code=500,
        media_type="application/json",
    )
