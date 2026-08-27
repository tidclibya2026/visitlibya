from sqlalchemy.orm import Session

from app.repositories.national_boundary import NationalBoundaryRepository


class NationalBoundaryService:

    def __init__(self, session: Session) -> None:
        self.repository = NationalBoundaryRepository(session)

    def get_public_boundary(
        self,
        country_code: str,
    ) -> dict | None:
        return self.repository.get_public_geojson(
            country_code.upper()
        )
