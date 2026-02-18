from fastapi import APIRouter, Depends
from fastapi.requests import Request

from crawlers.financial_yahoo import FinancialYahoo
from schemas.crawler import FinancialDataQueryParams

api = APIRouter(tags=["Crowler"])


@api.get("/financial-data")
async def get_financial_data(
    request: Request,
    params: FinancialDataQueryParams = Depends(),
):
    """Get data and generate info financial companies"""

    return await FinancialYahoo().generate_csv(
        request=request,
        region=params.region,
        max_pages=params.max_pages,
        headless=params.headless,
    )
