from fastapi import APIRouter, Depends
from fastapi.requests import Request

from crawlers.financial_yahoo import FinancialYahoo
from schemas.crawler import FinancialDataQueryParams

api = APIRouter(tags=["Crowler"])


@api.get("/financial-data")
def get_financial_data(
    request: Request,
    params: FinancialDataQueryParams = Depends(),
):
    """Get data and generate info financial companies"""

    return FinancialYahoo().generate_csv(
        request=request,
        region=params.region,
        max_pages=params.max_pages,
        headless=params.headless,
    )
