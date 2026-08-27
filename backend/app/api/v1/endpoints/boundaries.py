from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.national_boundary import NationalBoundaryFeature
from app.services.national_boundary import NationalBoundaryService


router = APIRouter(
    prefix="/gis/boundaries",
    tags=["GIS Boundaries"],
)


@router.get(
    "/libya",
    response_model=NationalBoundaryFeature,
)
def get_libya_boundary(
    session: Session = Depends(get_db),
) -> dict:
    service = NationalBoundaryService(session)

    boundary = service.get_public_boundary("LY")

    if boundary is None:
        raise HTTPException(
            status_code=404,
            detail="Published Libya national boundary is not available",
        )

    return boundary
