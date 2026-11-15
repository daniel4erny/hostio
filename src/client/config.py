import os

import typer


class HostioConfig:
    def __init__(self):
        configHome = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
        self.confFile = os.path.join(configHome, "hostio", "hostio.conf")
        self.confDir = os.path.dirname(self.confFile)
        if not os.path.exists(self.confDir):
            os.makedirs(self.confDir)
        if not os.path.exists(self.confFile):
            open(self.confFile, "w").close()

    def getValue(self, key: str) -> str:
        with open(self.confFile) as file:
            for line in file:
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip()

        return ""

    def setValue(self, key: str, value: str):
        changed_lines = []
        found = False
        with open(self.confFile) as file:
            for line in file:
                if not line.startswith(key + "="):
                    changed_lines.append(line)
                else:
                    found = True
                    changed_lines.append(f"{key}={value}\n")

        if not found:
            changed_lines.append(f"{key}={value}\n")

        with open(self.confFile, "w") as file:
            file.writelines(changed_lines)

    def __str__(self):
        with open(self.confFile) as file:
            return file.read()

    def getPath(self):
        return self.confFile


config = HostioConfig()

app = typer.Typer()


@app.command("set", help="set a config value for the client, valid keys are TOKEN and URL")
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

@app.command("info", help="show the current config values for the client and shows the path to it")
def info():
    print(config)
    print("Config path:", config.getPath())
