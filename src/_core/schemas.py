from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal


class CustomSearchParams(BaseModel):
    search: str = ""
    pageIndex: int = 1
    pageSize: Literal[10, 20, 30] = 10
    sortOption: Literal[0, 1] = 1
    culture: str = "fa-IR"
    fromDate: str = ""
    toDate: str = ""
    moduleId: int = 1286


class ResultAttributes(BaseModel):
    """Attributes for a search result item"""
    # Empty model as the Attributes field appears to be an empty object in the example


class ResultItem(BaseModel):
    """Individual result item within a search result"""

    Tags: List[str]
    DisplayModifiedTime: str
    AuthorProfileUrl: str
    AuthorName: Optional[str] = None
    Likes: int
    Comments: int
    Views: int
    Title: str
    Snippet: str
    Description: Optional[str] = None
    DocumentUrl: str
    DocumentTypeName: str
    Attributes: Dict[str, Any] = {}


class SearchResult(BaseModel):
    """Single search result entry"""

    DocumentUrl: str
    Title: str
    Results: List[ResultItem]


class SearchResponse(BaseModel):
    """Response model for the custom search API"""

    results: List[SearchResult]
    totalHits: int
    more: bool
