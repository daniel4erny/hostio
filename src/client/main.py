# CLIENT
import io
import json
import os
from pathlib import Path
from pprint import pprint
import tarfile
from lib.gitignore import is_gitignored

import config
import requests
import typer

app = typer.Typer()
app.add_typer(config.app, name="config", help="Hostio config commands")
conf = config.HostioConfig()



@app.command("init", help="init a project - folder copy via tar.gz to server")
def init(
    folder_path: str = typer.Argument(..., help="Path to the folder to send to server"),
    target_folder: str = typer.Argument(..., help="Target folder name on the server"),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-ow", help="If folder exists, you can rewrite it"
    ),
    gitignore: bool = typer.Option(
        False, "--gitignore", "-gi", help="If set, will ignore files in .gitignore"
    ),
    pushenv: bool = typer.Option(
        False, "--pushenv", "-pe", help="If set, will push .env file to server (will always even if gitignored)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
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
    def get_valid_files(base_path: Path, current_path: Path):
        for item in current_path.iterdir():
            if item.is_dir():
                get_valid_files(base_path, item)
            else:
                relative_path = item.relative_to(base_path)
                if gitignore and is_gitignored(base_path, relative_path):
                    if verbose:
                        pprint("IGNORING: " + str(relative_path))
                    continue
                if not pushenv and is_env_file(relative_path):
                    if verbose:
                        pprint("IGNORING: " + str(relative_path))
                    continue
                valid_files.append(relative_path)
    get_valid_files(upload_dir, upload_dir)

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        for index, file in enumerate(valid_files):
            tar.add(upload_dir / file, arcname=file)
            pprint("COMPRESSING PROGGRES: " + str(index + 1) + "/" + str(len(valid_files)) + " - " + str(file))
            if verbose:
                pprint("ADDING: " + str(file))

    tar_buffer.seek(0)

    headers = {"xtoken": conf.getValue("TOKEN")}
    url = conf.getValue("URL") + "/project/new"
    metadata = {"name": target_folder, "overwrite": overwrite}
    files = {"upload": ("upload.tar.gz", tar_buffer, "application/gzip")}

    # metadata: UploadMetadata = Form(...),
    # upload: UploadFile = File(...),
    # authorization=Depends(isUserAuthorized),
    response = requests.post(
        url,
        headers=headers,
        data=metadata,
        files=files,
        stream=True,
    )

    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                print(line.decode("utf-8"))
    else:
        print(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    app()
