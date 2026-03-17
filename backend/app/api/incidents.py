from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentDetailResponse,
    IncidentDraftGenerateRequest,
    IncidentDraftGenerateResponse,
    IncidentListItem,
    IncidentRead,
    IncidentUpdate,
)
from app.services.access_control import CurrentUser, require_permission
from app.services.ai_incidents import (
    IncidentDraftConfigurationError,
    IncidentDraftGenerationError,
    generate_incident_draft,
)
from app.services.incidents import create_incident, get_incident_detail, list_incidents_overview, update_incident


router = APIRouter()


@router.get("", response_model=list[IncidentListItem])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("incidents.view")),
) -> list[dict[str, object]]:
    return list_incidents_overview(db, current_user.access_context)


@router.post("/generate", response_model=IncidentDraftGenerateResponse)
def generate_incident_draft_endpoint(
    payload: IncidentDraftGenerateRequest,
    current_user: CurrentUser = Depends(require_permission("incidents.create")),
) -> IncidentDraftGenerateResponse:
    del current_user

    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    try:
        return generate_incident_draft(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IncidentDraftConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except IncidentDraftGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def incident_detail(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("incidents.view")),
) -> dict[str, object]:
    incident = get_incident_detail(db, incident_id, current_user.access_context)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentRead)
def create_incident_endpoint(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("incidents.create")),
) -> dict[str, object]:
    try:
        created = create_incident(
            db,
            current_user.access_context,
            incident.model_dump(),
            current_user.user.id if current_user.user else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    detail = get_incident_detail(db, created.id, current_user.access_context)
    if detail is None:
        raise HTTPException(status_code=500, detail="Incident created but could not be loaded")
    return detail


@router.patch("/{incident_id}", response_model=IncidentRead)
def update_incident_endpoint(
    incident_id: int,
    incident: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("incidents.update")),
) -> dict[str, object]:
    updated = update_incident(db, current_user.access_context, incident_id, incident.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    detail = get_incident_detail(db, updated.id, current_user.access_context)
    if detail is None:
        raise HTTPException(status_code=500, detail="Incident updated but could not be loaded")
    return detail
