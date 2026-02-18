from pydantic import BaseModel, Field


class FinancialDataQueryParams(BaseModel):
	region: str = Field(
		description="Region to be filtered in Yahoo Finance screener (example: brazil).",
		examples=["brazil"],
	)
	max_pages: int | None = Field(
		default=None,
		ge=1,
		description="Optional maximum number of pages to process.",
	)
	headless: bool = Field(
		default=False,
		description="Run browser in headless mode when true.",
	)


class FinancialRow(BaseModel):
	symbol: str
	name: str
	price: str


class FinancialDataResult(BaseModel):
	browser: str
	region: str
	max_pages: int | None = None
	headless: bool = False
	total_records: int
	data: list[FinancialRow]
