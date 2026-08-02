import logging
import sys
from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s",
                        stream=sys.stdout, force=True)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
