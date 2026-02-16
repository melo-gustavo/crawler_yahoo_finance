from fastapi import FastAPI
from routers import crawler

app = FastAPI()

app.include_router(crawler.api)
