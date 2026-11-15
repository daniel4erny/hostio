# SERVER
import os

import fastapi
from fastapi import Depends, File, Form, Header, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import tarfile
from dotenv import load_dotenv

load_dotenv() #for local dev

app = fastapi.FastAPI()
TOKEN: str = os.environ.get("TOKEN", "0")
if TOKEN == "0":
    raise ValueError("You have to set token first")
PROJECTS_DIR: str = os.environ.get("PROJECTS_DIR", "projects")


def isUserAuthorized(xtoken: str = Header(...)):
    if xtoken != TOKEN:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.get("/")
def home(authorization=Depends(isUserAuthorized)):
    return {"message": "Welcome to the server!"}

@app.post("/project/new")
def new(
    name: str = Form(...),
    overwrite: bool = Form(False),
    upload: UploadFile = File(...),
    authorization=Depends(isUserAuthorized),
):
    destination = os.path.join(PROJECTS_DIR, name)
    if os.path.exists(destination) and not overwrite:
        raise fastapi.HTTPException(
            status_code=400, detail="folder exists use -ow to overwrite"
        )

    async def unzipStream():
        msg = {"status": "GOT ALL FILES", "file": "START", "progress": f"{0}/{"X"}"}
        yield json.dumps(msg) + "\n"

        if not os.path.exists(destination):
            os.makedirs(os.path.join(PROJECTS_DIR, name))

        msg = {"status": "extracting", "file": "START", "progress": f"{0}/{"X"}"}
        yield json.dumps(msg) + "\n"
        with tarfile.open(fileobj=upload.file, mode="r:*") as tar:
            files = tar.getnames()
            total = len(files)

            for index, file in enumerate(files, start=1):
                tar.extract(file, destination, filter="data")

                msg = {"status": "extracting", "file": file, "progress": f"{index}/{total}"}
                yield json.dumps(msg) + "\n"

        yield json.dumps({"status": "done", "total_files": total}) + "\n"


    return StreamingResponse(unzipStream(), media_type="application/x-ndjson")
