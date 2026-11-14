#SERVER
import fastapi
from fastapi import Depends, Header
import os

app = fastapi.FastAPI()
TOKEN: str = os.environ.get("TOKEN", "0")
if TOKEN == "0":
    raise ValueError("You have to set token first")

def isUserAuthorized(xtoken: str = Header(...)):
    if xtoken != TOKEN:
        return False
    return True

@app.get("/")
def home(authorization=Depends(isUserAuthorized)):
    if not authorization:
        return fastapi.responses.JSONResponse(status_code=401, content={"message": "Unauthorized"})
    return {"message": "Welcome to the server!"}
