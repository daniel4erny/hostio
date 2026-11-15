import os

import typer


class HostioConfig:
    def __init__(self):
        self.confDir = os.path.join(os.path.expanduser("~"), ".hostio.conf")
        if not os.path.exists(self.confDir):
            os.makedirs(self.confDir)

    def getValue(self, key: str) -> str:
        with open(self.confDir) as file:
            for line in file:
                if line.startswith(key):
                    return line.split("=")[1].strip()

        return ""

    def setValue(self, key: str, value: str):
        changed_lines = []
        with open(self.confDir) as file:
            for line in file:
                if not line.startswith(key):
                    changed_lines.append(line)
                else:
                    changed_lines.append(f"{key}={value}\n")

        with open(self.confDir, "w") as file:
            file.writelines(changed_lines)

    def __str__(self):
        with open(self.confDir) as file:
            return file.read()


config = HostioConfig()

app = typer.Typer(help="Hostio config commands")


@app.command("set")
def set_config(
    key: str = typer.Argument(
        ..., help=
        """
        Specifies the key to which you want to assign \n
        TOKEN = the token to access the server \n
        URL = the url of the server \n
        """
    ),
    value: str = typer.Argument(
        ..., help="the value to whicht the key will be assigned"
    ),
):
    if key not in ["TOKEN", "URL"]:
        raise ValueError("Invalid key. Use help to see the available keys.")
    config.setValue(key, value)
    print(f"key {key} set to {value}")

@app.command("info")
def info():
    print(config)
