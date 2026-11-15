# CLIENT
import io
import os
import tarfile

import requests
import typer

import config

app = typer.Typer(help="Hostio client commands")
app.command("config")(config.app)

@app.command("deploy")
def init(
    folder_path: str = typer.Argument(..., help="Path to the folder to send to server"),
    target_folder: str = typer.Argument(..., help="Target folder name on the server"),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-ow", help="If folder exists, you can rewrite it"
    ),
):
    # 1 compress uzing tar.gz
    current_dir = os.getcwd()
    upload_dir = os.path.join(current_dir, folder_path)
    if not os.path.exists(upload_dir):
        raise ValueError(f"Folder {upload_dir} does not exist")

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        tar.add(
            upload_dir, arcname=os.path.basename(upload_dir), recursive=True
        )  # recursive is default True, this just makes it more readable

    tar_buffer.seek(0)
