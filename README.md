# edarehoquqy-crawler

A Simple Crawler for edarehoquqy.eadl.ir - a legal opinions database.

## Project Description

This project provides a web crawler for extracting legal opinions (نظریات مشورتی) from the edarehoquqy.eadl.ir website. It allows you to search for legal opinions with various parameters, supports pagination, and saves results as JSON files. The crawler is designed to be resumable, meaning it can continue from the last saved page in case of interruptions.

## Requirements

- Python 3.12 or higher
- Dependencies:
  - beautifulsoup4 >= 4.13.3
  - httpx >= 0.28.1
  - pydantic >= 2.10.6
  - pydantic-settings >= 2.8.1

## How to Use

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/edarehoquqy-crawler.git
cd edarehoquqy-crawler
```

2. Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

### Configuration

Create a `.env` file in the project root with the following settings:

```
OUTPUT_PATH=./data
```

This will determine where crawled data is saved.

### Basic Usage

```python
from src.handler import LegalOpinionsCrawler

# Initialize the crawler
crawler = LegalOpinionsCrawler()

# Search with specific parameters
results = crawler.crawl_all_results(
    search_text="قانون مدنی",  # Optional: search term
    page_size=10,              # Options: 10, 20, or 30
    sort_option=1,             # Options: 0 or 1
    from_date="1400/01/01",    # Optional: start date in Persian calendar
    to_date="1402/12/29"       # Optional: end date in Persian calendar
)

# Print number of results
print(f"Found {len(results)} opinions")
```

### Single Page Search

```python
from src._core.schemas import CustomSearchParams
from src.handler import LegalOpinionsCrawler

# Initialize the crawler
crawler = LegalOpinionsCrawler()
crawler.initialize_session()

# Create search parameters
params = CustomSearchParams(
    search="قانون تجارت",
    pageIndex=1,
    pageSize=20
)

# Perform search
response = crawler.search(params)

if response:
    print(f"Page 1 contains {len(response.results)} results")
    print(f"Total hits: {response.totalHits}")
```

## Schema

The crawler uses the following data models:

### CustomSearchParams

Parameters for searching legal opinions:

```python
class CustomSearchParams(BaseModel):
    search: str = ""             # Search term
    pageIndex: int = 1           # Page number
    pageSize: Literal[10, 20, 30] = 10  # Results per page
    sortOption: Literal[0, 1] = 1       # Sort method
    culture: str = "fa-IR"       # Culture/locale
    fromDate: str = ""           # Start date (e.g., "1400/01/01")
    toDate: str = ""             # End date (e.g., "1402/12/29")
    moduleId: int = 1286         # Module ID
```

### SearchResponse

Results from a search:

```python
class SearchResponse(BaseModel):
    results: List[SearchResult]  # Search results
    totalHits: int               # Total number of results
    more: bool                   # Whether more pages exist
```

### SearchResult

Individual search result:

```python
class SearchResult(BaseModel):
    DocumentUrl: str             # URL to the document
    Title: str                   # Title of the result
    Results: List[ResultItem]    # List of result items
```

### ResultItem

Detailed information about a legal opinion:

```python
class ResultItem(BaseModel):
    Tags: List[str]              # Tags associated with the opinion
    DisplayModifiedTime: str     # Modification time
    AuthorProfileUrl: str        # URL to author profile
    AuthorName: Optional[str]    # Name of the author
    Likes: int                   # Number of likes
    Comments: int                # Number of comments
    Views: int                   # Number of views
    Title: str                   # Title of the opinion
    Snippet: str                 # Short snippet/summary
    Description: Optional[str]   # Full description
    DocumentUrl: str             # URL to the document
    DocumentTypeName: str        # Type of the document
    Attributes: Dict[str, Any]   # Additional attributes
```
