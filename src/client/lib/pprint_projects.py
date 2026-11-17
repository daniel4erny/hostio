import colorama
from typing import TypedDict
from typing import Any

# id INTEGER PRIMARY KEY AUTOINCREMENT,
# created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
# name TEXT UNIQUE NOT NULL,
# path TEXT NOT NULL,
# status TEXT NOT NULL default 'not_built'


class Project(TypedDict):
    id: int
    created_at: str
    name: str
    path: str
    status: str

def pprint_projects(projects: list[Project]):
    if not projects:
        print(colorama.Fore.YELLOW + "No projects found" + colorama.Style.RESET_ALL)
        return

    print(
        colorama.Fore.CYAN
        + f"{'ID':<5} {'Name':<10} {'Created At':<25} {'Path':<25} {'Status':<50}"
        + colorama.Style.RESET_ALL
    )
    for p in projects:
        id_name = colorama.Fore.MAGENTA + f"{p["id"]:<5} {p["name"]:<10}"
        other = (
            colorama.Fore.LIGHTGREEN_EX
            + f"{p["created_at"]:<25} {p["path"]:<25} {p["status"]:<50}"
        )
        print(f"{id_name} {other}")
