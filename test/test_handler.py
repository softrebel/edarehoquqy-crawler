import unittest
from unittest.mock import patch, MagicMock
import json
import httpx
from src.handler import LegalOpinionsCrawler
from src._core.schemas import CustomSearchParams, SearchResponse


class TestLegalOpinionsCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = LegalOpinionsCrawler()

    @patch("httpx.Client.get")
    def test_initialize_session(self, mock_get):
        # Mock the response with a verification token
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <input name="__RequestVerificationToken" type="hidden" value="test-token-value" />
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock the cookies
        self.crawler.client.cookies = httpx.Cookies()
        self.crawler.client.cookies.set("test-cookie", "test-value")

        result = self.crawler.initialize_session()

        self.assertTrue(result)
        self.assertEqual(self.crawler.verification_token, "test-token-value")
        self.assertEqual(
            self.crawler.headers["requestverificationtoken"], "test-token-value"
        )
        self.assertEqual(mock_get.call_count, 1)

    @patch("httpx.Client.get")
    def test_initialize_session_failure(self, mock_get):
        # Mock a failed response
        mock_get.side_effect = httpx.RequestError("Connection error", request=None)

        result = self.crawler.initialize_session()

        self.assertFalse(result)
        self.assertIsNone(self.crawler.verification_token)

    @patch("handler.LegalOpinionsCrawler.initialize_session")
    @patch("httpx.Client.get")
    def test_search(self, mock_get, mock_init):
        # Mock successful initialization
        mock_init.return_value = True
        self.crawler.verification_token = "test-token"

        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"results": [], "totalHits": 0, "more": False}
        mock_get.return_value = mock_response

        params = CustomSearchParams(pageIndex=1, pageSize=10)
        result = self.crawler.search(params)

        self.assertIsNotNone(result)
        self.assertEqual(result.totalHits, 0)
        self.assertFalse(result.more)
        mock_get.assert_called_once()

    @patch("handler.LegalOpinionsCrawler.initialize_session")
    @patch("handler.LegalOpinionsCrawler.search")
    def test_crawl_all_results(self, mock_search, mock_init):
        # Mock successful initialization
        mock_init.return_value = True

        # Create mock search response with pagination
        first_page = SearchResponse(
            results=[{"DocumentUrl": "1", "Title": "Test 1", "Results": []}],
            totalHits=2,
            more=True,
        )

        second_page = SearchResponse(
            results=[{"DocumentUrl": "2", "Title": "Test 2", "Results": []}],
            totalHits=2,
            more=False,
        )

        # Search will be called twice, returning first page then second page
        mock_search.side_effect = [first_page, second_page]

        results = self.crawler.crawl_all_results()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["DocumentUrl"], "1")
        self.assertEqual(results[1]["DocumentUrl"], "2")
        self.assertEqual(mock_search.call_count, 2)

    @patch("handler.LegalOpinionsCrawler.initialize_session")
    def test_crawl_all_results_init_failure(self, mock_init):
        # Mock failed initialization
        mock_init.return_value = False

        results = self.crawler.crawl_all_results()

        self.assertEqual(len(results), 0)
        mock_init.assert_called_once()


if __name__ == "__main__":
    unittest.main()
