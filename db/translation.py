import logging
import time
from datetime import datetime, timedelta

from sqlalchemy import String, delete, select
from sqlalchemy.orm import mapped_column

import config
from db.engine import Base, session

logger = logging.getLogger(__name__)


class Translation(Base):
    __tablename__ = 'translation'

    source = mapped_column(String(65535), primary_key=True)
    target = mapped_column(String(65535))
    language = mapped_column(String(16))

    def __repr__(self):
        return f'<{self.source} - {self.target} - {self.language} - {self.access}>'


# TODO: enable other translation api
def get(text, to_lang):
    if to_lang == 'en':
        return text  # shortcut
    text = text[:Translation.source.type.length]
    stmt = select(Translation).where(Translation.source == text, Translation.language == to_lang)
    trans = session.scalars(stmt).first()
    if trans:
        trans.access = datetime.utcnow()
        # session.commit()  # Ok to batch it
        return trans.target
    return text


def add(source, target, lang):
    if not (source and target):
        return
    source = source[:Translation.source.type.length]
    target = target[:Translation.source.type.length]
    trans = Translation(source=source, target=target, language=lang, access=datetime.utcnow())
    session.merge(trans)  # source is primary key
    session.commit()


def expire():
    start = time.time()
    stmt = delete(Translation).where(
        Translation.access < datetime.utcnow() - timedelta(seconds=config.summary_ttl))
    result = session.execute(stmt)
    session.commit()
    cost = (time.time() - start) * 1000
    logger.info(f'evicted {result.rowcount} translation items, cost(ms): {cost:.2f}')
    return result.rowcount
