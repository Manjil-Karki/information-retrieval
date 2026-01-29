from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.apis.api import router

app = FastAPI(title="PUBLICATIONS SEARCH ENGINE API",
              description="An API for searching academic publications.",)

app.add_middleware(CORSMiddleware,
                allow_origins= ["*"],
                allow_credentials=True,
                allow_methods=["POST", "GET", "PUT", "OPTIONS", "PATH"],
                allow_headers=["Authorization", "Content-Type"])


app.include_router(router)