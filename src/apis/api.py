from fastapi import (
    APIRouter,
    Query
    
)

from typing import List


from src.utils.utils import search_publications

router = APIRouter()

@router.get(
    "/search",
    tags=["Search"],
    summary="Return top-k search results"
)
async def search_endpoint(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, description="Number of top results")
):
    return search_publications(query, top_n=k)