from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from ...models.user import User
from ...models.project import Project, ProjectMember
from ...models.brand_persona import BrandPersona
from ...models.project_api_key import ProjectApiKey
from ...schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectMemberAdd, ProjectMemberResponse,
    BrandPersonaUpdate, BrandPersonaResponse,
    ApiKeyCreate, ApiKeyResponse,
)
from ...services.crypto_service import encrypt_api_key, decrypt_api_key, mask_api_key
from ...api.deps import get_db, get_current_user, get_project_role, ROLE_HIERARCHY

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "admin":
        projects = db.exec(select(Project)).all()
    else:
        member_project_ids = db.exec(
            select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
        ).all()
        owned = db.exec(select(Project).where(Project.owner_id == user.id)).all()
        member_projects = db.exec(
            select(Project).where(Project.id.in_(member_project_ids))  # type: ignore
        ).all() if member_project_ids else []
        seen = set()
        projects = []
        for p in owned + member_projects:
            if p.id not in seen:
                seen.add(p.id)
                projects.append(p)
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot create projects")
    project = Project(
        name=data.name,
        domain=data.domain,
        description=data.description,
        business_type=data.business_type,
        owner_id=user.id,
    )
    db.add(project)
    # Create default brand persona
    persona = BrandPersona(project_id=project.id)
    db.add(persona)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = get_project_role(db, user, project_id)
    if ROLE_HIERARCHY.get(role or "", 0) < ROLE_HIERARCHY["strategist"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Strategist or admin access required")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only project owner or admin can delete")
    db.delete(project)
    db.commit()


# --- Members ---

@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def list_members(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    members = db.exec(select(ProjectMember).where(ProjectMember.project_id == project_id)).all()
    result = []
    for m in members:
        u = db.get(User, m.user_id)
        result.append(ProjectMemberResponse(
            id=m.id, project_id=m.project_id, user_id=m.user_id, role=m.role,
            user_email=u.email if u else None, user_name=u.full_name if u else None,
        ))
    return result


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=201)
def add_member(project_id: str, data: ProjectMemberAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = get_project_role(db, user, project_id)
    if ROLE_HIERARCHY.get(role or "", 0) < ROLE_HIERARCHY["strategist"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Strategist or admin access required to manage members")
    member = ProjectMember(project_id=project_id, user_id=data.user_id, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    u = db.get(User, member.user_id)
    return ProjectMemberResponse(
        id=member.id, project_id=member.project_id, user_id=member.user_id, role=member.role,
        user_email=u.email if u else None, user_name=u.full_name if u else None,
    )


# --- Brand Persona ---

@router.get("/{project_id}/persona", response_model=BrandPersonaResponse)
def get_persona(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == project_id)).first()
    if not persona:
        persona = BrandPersona(project_id=project_id)
        db.add(persona)
        db.commit()
        db.refresh(persona)
    return persona


@router.put("/{project_id}/persona", response_model=BrandPersonaResponse)
def update_persona(project_id: str, data: BrandPersonaUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = get_project_role(db, user, project_id)
    if ROLE_HIERARCHY.get(role or "", 0) < ROLE_HIERARCHY["strategist"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Strategist or admin access required")
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == project_id)).first()
    if not persona:
        persona = BrandPersona(project_id=project_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(persona, key, value)
    persona.updated_at = datetime.now(timezone.utc)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


# --- API Keys ---

@router.get("/{project_id}/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    keys = db.exec(select(ProjectApiKey).where(ProjectApiKey.project_id == project_id)).all()
    result = []
    for k in keys:
        plain = decrypt_api_key(k.encrypted_key)
        result.append(ApiKeyResponse(
            id=k.id, provider=k.provider, label=k.label,
            masked_key=mask_api_key(plain), created_at=str(k.created_at),
        ))
    return result


@router.post("/{project_id}/api-keys", response_model=ApiKeyResponse, status_code=201)
def add_api_key(project_id: str, data: ApiKeyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = get_project_role(db, user, project_id)
    if ROLE_HIERARCHY.get(role or "", 0) < ROLE_HIERARCHY["strategist"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Strategist or admin access required")
    # Upsert: if provider already exists for project, update it
    existing = db.exec(
        select(ProjectApiKey).where(
            ProjectApiKey.project_id == project_id,
            ProjectApiKey.provider == data.provider,
        )
    ).first()

    if existing:
        existing.encrypted_key = encrypt_api_key(data.api_key)
        existing.label = data.label
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        key_obj = ProjectApiKey(
            project_id=project_id,
            provider=data.provider,
            encrypted_key=encrypt_api_key(data.api_key),
            label=data.label,
        )
        db.add(key_obj)
        db.commit()
        db.refresh(key_obj)
        target = key_obj

    return ApiKeyResponse(
        id=target.id, provider=target.provider, label=target.label,
        masked_key=mask_api_key(data.api_key), created_at=str(target.created_at),
    )


@router.delete("/{project_id}/api-keys/{provider}", status_code=204)
def delete_api_key(project_id: str, provider: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = get_project_role(db, user, project_id)
    if ROLE_HIERARCHY.get(role or "", 0) < ROLE_HIERARCHY["strategist"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Strategist or admin access required")
    key = db.exec(
        select(ProjectApiKey).where(
            ProjectApiKey.project_id == project_id,
            ProjectApiKey.provider == provider,
        )
    ).first()
    if key:
        db.delete(key)
        db.commit()
