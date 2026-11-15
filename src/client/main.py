# CLIENT
import io
import json
import os
from pathlib import Path
import tarfile

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
):
    # 1 compress uzing tar.gz
    current_dir = Path(os.getcwd())
    upload_dir = current_dir / Path(folder_path)
    if not os.path.exists(upload_dir):
        raise ValueError(f"Folder {upload_dir} does not exist")

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        tar.add(
            upload_dir, arcname="", recursive=True
        )  # recursive is default True, this just makes it more readable

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
