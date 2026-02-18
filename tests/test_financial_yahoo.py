from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import Response

from crawlers.financial_yahoo import FinancialYahoo
from schemas.crawler import FinancialDataResult, FinancialRow


def test_extract_table_data_parses_rows_from_html():
    crawler = FinancialYahoo()
    driver = Mock()
    driver.page_source = """
    <table>
      <thead>
        <tr><th>Symbol</th><th>Name</th><th>Price</th></tr>
      </thead>
      <tbody>
        <tr><td>ITUB4.SA</td><td>Itaú Unibanco</td><td>47.77</td></tr>
        <tr><td>PETR4.SA</td><td>Petrobras</td><td>36.10</td></tr>
      </tbody>
    </table>
    """

    data = crawler._extract_table_data(driver)

    assert len(data) == 2
    assert data[0].symbol == "ITUB4.SA"
    assert data[0].name == "Itaú Unibanco"


def test_get_attrs_rejects_invalid_max_pages():
    crawler = FinancialYahoo()
    request = Mock()

    with pytest.raises(HTTPException) as exc:
        crawler.get_attrs(request=request, region="brazil", max_pages=0, headless=False)

    assert exc.value.status_code == 400


def test_generate_csv_returns_bom_and_content():
    crawler = FinancialYahoo()
    request = Mock()

    fake_result = FinancialDataResult(
        browser="Chrome",
        region="Brazil",
        max_pages=1,
        headless=True,
        total_records=1,
        data=[FinancialRow(symbol="ITUB4.SA", name="Itaú Unibanco", price="47.77")],
    )

    with patch.object(FinancialYahoo, "get_attrs", return_value=fake_result):
        response = crawler.generate_csv(
            request=request, region="brazil", max_pages=1, headless=True
        )

    assert isinstance(response, Response)
    assert response.media_type == "text/csv; charset=utf-8"
    assert b"ITUB4.SA" in response.body
