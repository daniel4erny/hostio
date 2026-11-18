# CLIENT
import io
import json
import os
import tarfile
from pathlib import Path
from pprint import pprint

import config
import requests
import tqdm
import typer
from typer_alias import command
from lib.gitignore import is_gitignored
from lib.pprint_projects import pprint_projects

app = typer.Typer()
app.add_typer(config.app, name="config", help="Hostio config commands")
conf = config.HostioConfig()


@command(app, name="init", help="init a project - folder copy via tar.gz to server")
def init(
    folder_path: str = typer.Argument(..., help="Path to the folder to send to server"),
    target_folder: str = typer.Argument(..., help="Target folder name on the server"),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-ow", help="If folder exists, you can rewrite it"
    ),
    ignoregit: bool = typer.Option(
        False, "--ignoregit", "-ig", help="If set, will ignore files in .gitignore"
    ),
    pushenv: bool = typer.Option(
        False,
        "--pushenv",
        "-pe",
        help="If set, will push .env file to server (will always even if gitignored)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    if ignoregit:
        pprint("pushnig gitignored files")
    if pushenv:
        pprint("pushing .env files")
    # 1 compress uzing tar.gz
    current_dir = Path(os.getcwd())
    upload_dir = current_dir / Path(folder_path)
    if not os.path.exists(upload_dir):
        raise ValueError(f"Folder {upload_dir} does not exist")

    def is_env_file(path: Path) -> bool:
        name = path.name
        return name == ".env" or (
            name.startswith(".env.")
            and not name.endswith((".example", ".sample", ".template"))
        )

    valid_files = []
    scan_bar = tqdm.tqdm(desc="Scanning files", unit=" entry")

    def get_valid_files(base_path: Path, current_path: Path):
        for item in current_path.iterdir():
            scan_bar.update(1)
            if item.name == ".git":
                if verbose:
                    pprint("IGNORING: " + str(item.relative_to(base_path)))
                continue
            if item.is_dir():
                get_valid_files(base_path, item)
            else:
                relative_path = item.relative_to(base_path)
                if not ignoregit and is_gitignored(base_path, relative_path):
                    if verbose:
                        pprint("IGNORING: " + str(relative_path))
                    continue
                if not pushenv and is_env_file(relative_path):
                    if verbose:
                        pprint("IGNORING: " + str(relative_path))
                    continue
                valid_files.append(relative_path)

    get_valid_files(upload_dir, upload_dir)
    scan_bar.close()

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        for file in tqdm.tqdm(
            valid_files, total=len(valid_files), desc="Compressing files", unit=" file"
        ):
            tar.add(upload_dir / file, arcname=file)
            if verbose:
                pprint("ADDING: " + str(file))

    tar_buffer.seek(0)

    headers = {"xtoken": conf.getValue("TOKEN")}
    url = conf.getValue("URL") + "/projects/new"
    metadata = {"name": target_folder, "overwrite": overwrite}
    files = {"upload": ("upload.tar.gz", tar_buffer, "application/gzip")}

    # metadata: UploadMetadata = Form(...),
    # upload: UploadFile = File(...),
    # authorization=Depends(isUserAuthorized),
    pprint(f"Uploading to {url}")
    response = requests.post(
        url,
        headers=headers,
        data=metadata,
        files=files,
        stream=True,
    )

    if response.status_code == 200:
        errors = 0
        skipped = 0
        for line in tqdm.tqdm(
            response.iter_lines(),
            total=len(valid_files) + 2,  # server sends START + one line per file + done
            desc="decompressing on server side",
            unit=" file",
        ):
            if not line:
                continue
            text = line.decode("utf-8")
            if verbose:
                tqdm.tqdm.write(text)
            try:
                message = json.loads(text)
            except json.JSONDecodeError:
                continue
            if message.get("status") == "error":
                errors += 1
            elif message.get("status") == "skipped":
                skipped += 1

        if skipped:
            print(f"Warning: server skipped {skipped} file(s), see above")
        if errors:
            raise typer.Exit(code=1)
    else:
        print(f"Error: {response.status_code} - {response.text}")
        raise typer.Exit(code=1)


@command(app, name="list", aliases=["ls", "l"], help="list projects on server")
def list_projects():
    headers = {"xtoken": conf.getValue("TOKEN")}
    url = conf.getValue("URL") + "/projects/list"
    pprint(f"Fetching projects from {url}")
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        raise ValueError(f"{e} \n\n Perhaps you dont have config set up, use hostio config")
    if response.status_code == 200:
        projects = response.json()
        pprint_projects(projects)
    else:
        print(f"Error: {response.status_code} - {response.text}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
