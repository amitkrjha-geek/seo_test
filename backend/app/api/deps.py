from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from ..database import get_session
from ..models.user import User
from ..models.project import Project, ProjectMember
from ..services.auth_service import decode_token

security = HTTPBearer()

# Role hierarchy: admin > strategist > writer > client
ROLE_HIERARCHY = {"admin": 4, "strategist": 3, "writer": 2, "client": 1}


def get_db():
    yield from get_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_strategist_or_above(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "strategist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Strategist or admin access required")
    return user


def require_writer_or_above(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "strategist", "writer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Writer access or above required")
    return user


def get_project_role(db: Session, user: User, project_id: str) -> str | None:
    """Return the effective role a user has on a project (owner counts as admin)."""
    if user.role == "admin":
        return "admin"
    project = db.get(Project, project_id)
    if not project:
        return None
    if project.owner_id == user.id:
        return "admin"
    member = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    ).first()
    return member.role if member else None


def require_project_access(
    project_id: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Verify user has any access to the given project (is owner, member, or global admin)."""
    role = get_project_role(db, user, project_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this project")
    return user


def require_project_write(
    project_id: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Verify user has writer-or-above access on the project (clients are read-only)."""
    role = get_project_role(db, user, project_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this project")
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY["writer"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access required")
    return user
