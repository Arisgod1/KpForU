from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.errors import http_error
from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.timeflow import TimeFlowTemplate
from app.schemas.timeflow import (
    PaginatedTimeFlowTemplates,
    TimeFlowTemplate as TimeFlowTemplateSchema,
    TimeFlowTemplateCreate,
)

router = APIRouter(tags=["TimeFlow"])


@router.post("/timeflows/templates", response_model=TimeFlowTemplateSchema, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TimeFlowTemplateCreate,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    payload_dict = payload.model_dump()
    template = TimeFlowTemplate(
        user_id=user.id,
        name=payload.name,
        phases=payload_dict["phases"],
        loop=payload_dict["loop"],
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TimeFlowTemplateSchema(
        id=str(template.id),
        name=template.name,
        phases=payload.phases,
        loop=payload.loop,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/timeflows/templates", response_model=PaginatedTimeFlowTemplates)
def list_templates(
    limit: int = Query(default=20, le=100),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    query = db.query(TimeFlowTemplate).filter(TimeFlowTemplate.user_id == user.id).order_by(TimeFlowTemplate.created_at.desc())
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.filter(TimeFlowTemplate.created_at < cursor_dt)
        except ValueError:
            pass
    items = query.limit(limit + 1).all()
    next_cursor = None
    if len(items) > limit:
        next_cursor = items[-1].created_at.isoformat()
        items = items[:limit]
    data = [
        TimeFlowTemplateSchema(
            id=str(t.id),
            name=t.name,
            phases=t.phases,
            loop=t.loop,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in items
    ]
    return PaginatedTimeFlowTemplates(data=data, next_cursor=next_cursor)


@router.put("/timeflows/templates/{template_id}", response_model=TimeFlowTemplateSchema)
def update_template(
    template_id: UUID,
    payload: TimeFlowTemplateCreate,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    template = db.query(TimeFlowTemplate).filter(TimeFlowTemplate.id == template_id, TimeFlowTemplate.user_id == user.id).first()
    if template is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Template not found")
    payload_dict = payload.model_dump()
    template.name = payload.name
    template.phases = payload_dict["phases"]
    template.loop = payload_dict["loop"]
    db.commit()
    db.refresh(template)
    return TimeFlowTemplateSchema(
        id=str(template.id),
        name=template.name,
        phases=template.phases,
        loop=template.loop,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/timeflows/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    template = db.query(TimeFlowTemplate).filter(TimeFlowTemplate.id == template_id, TimeFlowTemplate.user_id == user.id).first()
    if template is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Template not found")
    db.delete(template)
    db.commit()
    return None
