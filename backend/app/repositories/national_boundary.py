from sqlalchemy import func, select

from app.models.national_boundary import NationalBoundary
from app.repositories.base import BaseRepository


class NationalBoundaryRepository(BaseRepository[NationalBoundary]):

    def get_by_country_code(
        self,
        country_code: str,
    ) -> NationalBoundary | None:
        statement = select(NationalBoundary).where(
            NationalBoundary.country_code == country_code.upper()
        )
        return self.session.scalar(statement)

    def get_published_by_country_code(
        self,
        country_code: str,
    ) -> NationalBoundary | None:
        statement = select(NationalBoundary).where(
            NationalBoundary.country_code == country_code.upper(),
            NationalBoundary.is_validated.is_(True),
            NationalBoundary.is_published.is_(True),
            NationalBoundary.geometry.is_not(None),
        )
        return self.session.scalar(statement)

    def get_public_geojson(
        self,
        country_code: str,
    ) -> dict | None:
        statement = (
            select(
                NationalBoundary.id,
                NationalBoundary.country_code,
                NationalBoundary.name_en,
                NationalBoundary.name_ar,
                func.ST_AsGeoJSON(
                    NationalBoundary.geometry,
                    6,
                ).label("geometry"),
            )
            .where(
                NationalBoundary.country_code == country_code.upper(),
                NationalBoundary.is_validated.is_(True),
                NationalBoundary.is_published.is_(True),
            )
        )

        row = self.session.execute(statement).mappings().first()

        if row is None:
            return None

        import json

        return {
            "type": "Feature",
            "id": row["id"],
            "properties": {
                "country_code": row["country_code"],
                "name_en": row["name_en"],
                "name_ar": row["name_ar"],
            },
            "geometry": json.loads(row["geometry"]),
        }

    def geometry_is_valid(
        self,
        boundary: NationalBoundary,
    ) -> bool:
        statement = select(
            func.ST_IsValid(boundary.geometry)
        )
        return bool(self.session.scalar(statement))

    def geometry_srid(
        self,
        boundary: NationalBoundary,
    ) -> int | None:
        statement = select(
            func.ST_SRID(boundary.geometry)
        )
        return self.session.scalar(statement)
