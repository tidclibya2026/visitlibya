import pytest
from pydantic import ValidationError

from app.schemas.destination import DestinationCreate, DestinationUpdate


@pytest.mark.parametrize("field", ["publication_approved", "institutional_decision", "evidence_reference"])
def test_client_cannot_supply_approval_fields(field):
    payload = {"slug": "synthetic", "translations": [{"language_code": "en", "name": "Synthetic"}], field: True}
    with pytest.raises(ValidationError): DestinationCreate.model_validate(payload)
    with pytest.raises(ValidationError): DestinationUpdate.model_validate({field: True})
