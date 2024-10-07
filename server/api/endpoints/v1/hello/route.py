# server/api/endpoints/v1/hello-world/first-come.py

from fastapi import APIRouter

router = APIRouter(tags=["hello-world"])

@router.get("/")
async def first_come():
    return {"message": "Hello, World!"}

