# server/run.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints.v1.hello.route import router as hello_router
from api.endpoints.v1.auth.route import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello_router)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=3232, reload=True)

