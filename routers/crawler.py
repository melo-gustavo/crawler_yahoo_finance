from fastapi import APIRouter
from fastapi.requests import Request

from crawlers.financial_yahoo import FinancialYahoo

api = APIRouter(tags=["Crowler"])


@api.get("/financial-data")
def get_financial_data(request: Request, region: str):
    """Get data and generate info financial companies"""

    return FinancialYahoo().generate_csv(request, region)
