from fastapi import APIRouter, Query

from ..services.recommendations import youtube_recommendations, website_recommendations


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/youtube")
def recs_youtube(q: str = Query(..., description="Search keyword")):
    return youtube_recommendations(q)


@router.get("/web")
def recs_web(q: str = Query(..., description="Query for related websites")):
    return website_recommendations(q)


