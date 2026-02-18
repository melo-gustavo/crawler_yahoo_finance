import asyncio
from unittest.mock import AsyncMock, Mock, patch

from routers.crawler import get_financial_data
from schemas.crawler import FinancialDataQueryParams


def test_get_financial_data_calls_generate_csv_with_schema_params():
    request = Mock()
    params = FinancialDataQueryParams(region="brazil", max_pages=2, headless=True)

    expected_response = Mock()

    with patch("routers.crawler.FinancialYahoo") as crawler_cls:
        crawler_instance = crawler_cls.return_value
        crawler_instance.generate_csv = AsyncMock(return_value=expected_response)

        response = asyncio.run(get_financial_data(request=request, params=params))

    assert response is expected_response
    crawler_instance.generate_csv.assert_awaited_once_with(
        request=request,
        region="brazil",
        max_pages=2,
        headless=True,
    )
