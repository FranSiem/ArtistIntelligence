"""GET /api/search/artists"""

import logging
from fastapi import APIRouter, Query
from app.services import chartmetric

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search/artists")
async def search_artists(q: str = Query(..., min_length=1)):
    log.info("search q=%r", q)
    try:
        results = await chartmetric.search_artists(q)
        log.info("search returned %d results", len(results))
        return results
    except Exception:
        log.exception("search failed")
        raise
