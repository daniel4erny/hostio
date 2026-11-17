# SERVER
from contextlib import asynccontextmanager
import json
import os
import re
import secrets
import shutil
import tarfile
import tempfile
import asyncio
import aiodocker

import fastapi
from dotenv import load_dotenv
from fastapi import Depends, File, Form, Header, Request, UploadFile
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from db_lib.db import Database

load_dotenv()  # for local dev

TOKEN: str = os.environ.get("TOKEN", "0")
if TOKEN == "0":
    raise ValueError("You have to set token first")
PROJECTS_DIR: str = os.path.realpath(os.environ.get("PROJECTS_DIR", "projects"))
os.makedirs(PROJECTS_DIR, exist_ok=True)

MAX_UPLOAD_MB: int = int(os.environ.get("MAX_UPLOAD_MB", "2048"))

TEMP_PREFIX = ".tmp-"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    db = Database()
    await db.init()
    app.state.db = db
    try:
        yield
    finally:
        await db.close()

def resolve_project(name: str) -> str:
    if not NAME_PATTERN.fullmatch(name):
        raise fastapi.HTTPException(
            status_code=400,
            detail=(
                "invalid project name: use letters, digits, '.', '_' or '-' "
                "(max 100 chars, must not start with '.')"
            ),
        )
    destination = os.path.realpath(os.path.join(PROJECTS_DIR, name))
    if os.path.commonpath([destination, PROJECTS_DIR]) != PROJECTS_DIR:
        raise fastapi.HTTPException(status_code=400, detail="invalid project name")
    return destination


app = fastapi.FastAPI(lifespan=lifespan)


def isUserAuthorized(xtoken: str | None = Header(None)):
    if not xtoken or not secrets.compare_digest(xtoken, TOKEN):
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
    return True


def event(status: str, file: str, index: int, total: int) -> str:
    return (
        json.dumps({"status": status, "file": file, "progress": f"{index}/{total}"})
        + "\n"
    )


@app.get("/projects/list")
async def home(authorization=Depends(isUserAuthorized)):
    if type(app.state.db) is not Database:
        raise fastapi.HTTPException(status_code=500, detail="Database error")
    return await app.state.db.listProjects()


@app.post("/projects/new")
async def new(
    request: Request,
    name: str = Form(...),
    overwrite: bool = Form(False),
    upload: UploadFile = File(...),
    authorization=Depends(isUserAuthorized),
):
    destination = resolve_project(name)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            too_big = int(content_length) > MAX_UPLOAD_MB * 1024 * 1024
        except ValueError:
            too_big = True
        if too_big:
            raise fastapi.HTTPException(
                status_code=413, detail=f"upload exceeds {MAX_UPLOAD_MB} MB"
            )

    if os.path.exists(destination) and not overwrite:
        raise fastapi.HTTPException(
            status_code=400, detail="folder exists use -ow to overwrite"
        )

    def openTar(file, mode):
        try:
            tar = tarfile.open(fileobj=file, mode=mode)
            members = tar.getmembers()
            return (members, tar)
        except tarfile.TarError as e:
            raise fastapi.HTTPException(status_code=400, detail=f"invalid archive: {e}")

    members, tar = await run_in_threadpool(openTar, upload.file, "r:*")

    os.makedirs(PROJECTS_DIR, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=PROJECTS_DIR)

    async def unzipStream():
        total = len(members)

        try:
            yield event("extracting", "START", 0, total)

            for index, member in enumerate(members, start=1):
                await asyncio.to_thread(tar.extract, member, tmp_dir, filter="data")
                yield event("extracting", member.name, index, total)

            if os.path.exists(destination):
                shutil.rmtree(destination)
            os.replace(tmp_dir, destination)

            if type(request.app) is not fastapi.FastAPI:
                raise ValueError("tf lol")

            db = request.app.state.db
            await db.initProject(name, destination)

            yield json.dumps({"status": "done", "total_files": total}) + "\n"
        except Exception as e:
            yield json.dumps({"status": "error", "detail": str(e)}) + "\n"
        finally:
            tar.close()
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return StreamingResponse(unzipStream(), media_type="application/x-ndjson")

#THIS USES DOCKER DOWN BELOW
@app.get("/docker/check")
async def check_docker(authorization=Depends(isUserAuthorized)):
    docker = aiodocker.Docker()
    try:
        version = await docker.version()
        return {"status": "ok", "version": version}
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=f"Docker error: {e}")
