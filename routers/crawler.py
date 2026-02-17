from fastapi import APIRouter
from fastapi.requests import Request

from crawlers.financial_yahoo import FinancialYahoo

api = APIRouter(tags=["Crowler"])


@api.get("/financial-data")
async def get_financial_data(
    request: Request,
    region: str,
    max_pages: int | None = None,
    headless: bool = False,
):
    """Get data and generate info financial companies"""

    return await FinancialYahoo().generate_csv(
        request=request,
        region=region,
        max_pages=max_pages,
        headless=headless,
    )
