# SERVER
import os

import fastapi
from fastapi import Depends, File, Form, Header, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import zipfile

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


class UploadMetadata(BaseModel):
    target_folder: str
    overwrite: bool = False


@app.post("/project/new")
def new(
    metadata: UploadMetadata = Form(...),
    upload: UploadFile = File(...),
    authorization=Depends(isUserAuthorized),
):
    destination = os.path.join(PROJECTS_DIR, metadata.target_folder)

    async def unzipStream():
        if os.path.exists(destination) and not metadata.overwrite:
            raise fastapi.HTTPException(
                status_code=400, detail="folder exists use -ow to overwrite"
            )

        if not os.path.exists(destination):
            os.makedirs(os.path.join(PROJECTS_DIR, metadata.target_folder))

        msg = {"status": "extracting", "file": "START", "progress": f"{0}/{"X"}"}
        with zipfile.ZipFile(upload.file) as zip_file:
            files = zip_file.namelist()
            total = len(files)

            for index, file in enumerate(files, start=1):
                zip_file.extract(file, destination)

                msg = {"status": "extracting", "file": file, "progress": f"{index}/{total}"}
                yield json.dumps(msg) + "\n"

        yield json.dumps({"status": "done", "total_files": total}) + "\n"


    return StreamingResponse(unzipStream(), media_type="application/x-ndjson")
