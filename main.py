from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import Base, engine
from auth_routes import router

app = FastAPI()


# CORS FIX (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DATABASE

Base.metadata.create_all(bind=engine)


# ROUTES
app.include_router(router)
