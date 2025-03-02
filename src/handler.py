import httpx
from bs4 import BeautifulSoup
import logging
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import ValidationError
from src._core.schemas import CustomSearchParams, SearchResponse
from src._core import project_configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalOpinionsCrawler:
    """Crawler for legal opinions from edarehoquqy.eadl.ir"""

    BASE_URL = "https://edarehoquqy.eadl.ir"
    SEARCH_PAGE_URL = f"{BASE_URL}/%D8%AC%D8%B3%D8%AA%D8%AC%D9%88%DB%8C-%D9%86%D8%B8%D8%B1%DB%8C%D8%A7%D8%AA-%D9%85%D8%B4%D9%88%D8%B1%D8%AA%DB%8C/%D8%AC%D8%B3%D8%AA%D8%AC%D9%88%DB%8C-%D9%86%D8%B8%D8%B1%DB%8C%D9%87"
    SEARCH_API_URL = f"{BASE_URL}/API/Mvc/IdeaProject.IdeaSearch/CustomSearch/Search"

    def __init__(self):
        self.client = httpx.Client(follow_redirects=True)
        self.verification_token = None
        self.cookies = {}
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "moduleid": "1286",
            "priority": "u=1, i",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "tabid": "495",
        }

    def __del__(self):
        """Close the client when the object is destroyed"""
        if hasattr(self, "client") and self.client:
            self.client.close()

    def initialize_session(self) -> bool:
        """
        Initialize the session by visiting the search page and obtaining the verification token

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        try:
            response = self.client.get(self.SEARCH_PAGE_URL)
            response.raise_for_status()

            # Parse the page to get the verification token
            soup = BeautifulSoup(response.text, "html.parser")
            token_input = soup.select_one('input[name="__RequestVerificationToken"]')

            if not token_input:
                logger.error("Verification token not found in the page")
                return False

            self.verification_token = token_input.get("value")
            self.cookies = {k: v for k, v in self.client.cookies.items()}

            # Add the token to the headers
            self.headers["requestverificationtoken"] = self.verification_token
            self.headers["referer"] = self.SEARCH_PAGE_URL

            logger.info(
                f"Session initialized successfully with token: {self.verification_token[:10]}..."
            )
            return True

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to initialize session: {e}")
            return False

    def save_results_to_json(
        self, data: Dict[str, Any], page_number: int, params: Dict[str, Any]
    ) -> Optional[str]:
        """
        Save the results to a JSON file

        Args:
            data: The data to save
            page_number: The page number
            params: The search parameters used

        Returns:
            Optional[str]: The path to the saved file or None if OUTPUT_PATH is not configured
        """
        if not project_configs.OUTPUT_PATH:
            logger.warning("OUTPUT_PATH is not configured. Results not saved to file.")
            return None

        # Create a filename with search parameters
        search_term = params.get("search", "")
        search_term_part = f"_{search_term}" if search_term else ""
        from_date = params.get("fromDate", "")
        to_date = params.get("toDate", "")
        date_part = f"_{from_date}_to_{to_date}" if from_date or to_date else ""

        filename = f"legal_opinions{search_term_part}{date_part}_page{page_number}.json"
        file_path = Path(project_configs.OUTPUT_PATH) / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            logger.info(f"Saved results to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save results to file: {e}")
            return None

    def get_saved_file_path(self, page_number: int, params: Dict[str, Any]) -> Optional[Path]:
        """
        Get the file path for a saved page

        Args:
            page_number: The page number
            params: The search parameters used

        Returns:
            Optional[Path]: The path to the saved file or None if OUTPUT_PATH is not configured
        """
        if not project_configs.OUTPUT_PATH:
            return None

        search_term = params.get("search", "")
        search_term_part = f"_{search_term}" if search_term else ""
        from_date = params.get("fromDate", "")
        to_date = params.get("toDate", "")
        date_part = f"_{from_date}_to_{to_date}" if from_date or to_date else ""

        filename = f"legal_opinions{search_term_part}{date_part}_page{page_number}.json"
        return Path(project_configs.OUTPUT_PATH) / filename

    def load_saved_search_response(self, file_path: Path) -> Optional[SearchResponse]:
        """
        Load a saved search response from a file

        Args:
            file_path: Path to the saved file

        Returns:
            Optional[SearchResponse]: The loaded search response or None if loading fails
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            try:
                return SearchResponse.model_validate(data)
            except ValidationError as e:
                logger.error(f"Failed to parse saved search response: {e}")
                return None
        except Exception as e:
            logger.error(f"Failed to load saved search response: {e}")
            return None

    def search(self, params: CustomSearchParams) -> Optional[SearchResponse]:
        """
        Perform a search using the given parameters

        Args:
            params: CustomSearchParams with search parameters

        Returns:
            Optional[SearchResponse]: The search response or None if the request failed
        """
        if not self.verification_token:
            if not self.initialize_session():
                return None

        # Check if we already have this page saved
        params_dict = params.model_dump()
        file_path = self.get_saved_file_path(params_dict["pageIndex"], params_dict)

        if file_path and file_path.exists():
            logger.info(f"Found saved results for page {params_dict['pageIndex']}, loading from file")
            return self.load_saved_search_response(file_path)

        try:
            response = self.client.get(
                self.SEARCH_API_URL,
                params=params_dict,
                headers=self.headers,
                cookies=self.cookies,
            )
            response.raise_for_status()

            # Save the raw JSON response to a file
            response_data = response.json()
            self.save_results_to_json(
                response_data,
                params_dict["pageIndex"],
                params_dict
            )

            try:
                search_response = SearchResponse.model_validate(response_data)
                logger.info(
                    f"Search successful, found {search_response.totalHits} results"
                )
                return search_response
            except ValidationError as e:
                logger.error(f"Failed to parse search response: {e}")
                return None

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Search request failed: {e}")
            return None

    def crawl_all_results(
        self,
        search_text: str = "",
        page_size: int = 10,
        sort_option: int = 1,
        from_date: str = "",
        to_date: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Crawl all search results with pagination, skipping already saved pages

        Args:
            search_text: Text to search for
            page_size: Number of results per page (10, 20, or 30)
            sort_option: Sort option (0 or 1)
            from_date: Start date for filtering
            to_date: End date for filtering

        Returns:
            List of all search results
        """
        all_results = []
        current_page = 1
        has_more = True
        last_saved_page = self.find_last_saved_page(search_text, page_size, sort_option, from_date, to_date)

        if last_saved_page > 0:
            logger.info(f"Found previously saved results up to page {last_saved_page}")
            current_page = last_saved_page

            # Load results from the last saved page to check if there are more pages
            params = CustomSearchParams(
                search=search_text,
                pageIndex=current_page,
                pageSize=page_size,
                sortOption=sort_option,
                fromDate=from_date,
                toDate=to_date,
            )

            file_path = self.get_saved_file_path(current_page, params.model_dump())
            if file_path and file_path.exists():
                search_response = self.load_saved_search_response(file_path)
                if search_response:
                    all_results.extend(search_response.results)
                    has_more = search_response.more
                    if has_more:
                        current_page += 1

        # Initialize the session before starting new requests
        if has_more and not self.verification_token:
            if not self.initialize_session():
                logger.error("Failed to initialize session, aborting crawl")
                return all_results

        while has_more:
            logger.info(f"Fetching page {current_page}")

            params = CustomSearchParams(
                search=search_text,
                pageIndex=current_page,
                pageSize=page_size,
                sortOption=sort_option,
                fromDate=from_date,
                toDate=to_date,
            )

            search_response = self.search(params)

            if not search_response:
                logger.error(
                    f"Failed to get results for page {current_page}, stopping pagination"
                )
                break

            # Add the results from this page
            all_results.extend(search_response.results)

            # Check if there are more pages
            has_more = search_response.more

            if has_more:
                current_page += 1

        logger.info(f"Crawling completed, collected {len(all_results)} total results")
        return all_results

    def find_last_saved_page(
        self,
        search_text: str = "",
        page_size: int = 10,
        sort_option: int = 1,
        from_date: str = "",
        to_date: str = ""
    ) -> int:
        """
        Find the last saved page number for the given search parameters

        Args:
            search_text: Text to search for
            page_size: Number of results per page
            sort_option: Sort option
            from_date: Start date for filtering
            to_date: End date for filtering

        Returns:
            int: The last saved page number, or 0 if no pages are saved
        """
        if not project_configs.OUTPUT_PATH:
            return 0

        # Create the pattern for matching filenames
        search_term_part = f"_{search_text}" if search_text else ""
        date_part = f"_{from_date}_to_{to_date}" if from_date or to_date else ""
        pattern = f"legal_opinions{search_term_part}{date_part}_page"

        # Find all matching files
        last_page = 0
        output_dir = Path(project_configs.OUTPUT_PATH)

        if not output_dir.exists():
            return 0

        for file_path in output_dir.glob(f"{pattern}*.json"):
            try:
                # Extract page number from filename
                filename = file_path.name
                page_str = filename.split('_page')[1].split('.json')[0]
                page_num = int(page_str)
                last_page = max(last_page, page_num)
            except (ValueError, IndexError):
                continue

        return last_page
