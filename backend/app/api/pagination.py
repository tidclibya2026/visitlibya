from typing import Annotated

from fastapi import Query


SkipParameter = Annotated[int, Query(ge=0)]
LimitParameter = Annotated[int, Query(ge=1, le=100)]
