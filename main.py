import requests
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

PYTHON = "3.11"
checked = not_found = incompatible = 0
highest = None

with open("requirements2.txt") as f:
    for line in f:
        line = line.split("#")[0].strip()
        if not line:
            continue

        try:
            req = Requirement(line)
            if req.marker and not req.marker.evaluate(
                {"python_version": PYTHON, "python_full_version": "3.11.0"}
            ):
                continue

            checked += 1
            if req.url:
                not_found += 1
                continue

            data = requests.get(f"https://pypi.org/pypi/{req.name}/json", timeout=15)

            if data.status_code == 404:
                not_found += 1
                continue
            data.raise_for_status()
            data = data.json()

            versions = []
            for v, files in data["releases"].items():
                try:
                    if (
                        files
                        and req.specifier.contains(v)
                        and any(not x["yanked"] for x in files)
                    ):
                        versions.append(Version(v))
                except (InvalidVersion, KeyError):
                    pass

            if not versions:
                not_found += 1
                continue

            version = max(versions)
            files = data["releases"][str(version)]
            python_reqs = [
                x["requires_python"]
                for x in files
                if x.get("requires_python") and not x.get("yanked")
            ]

            if python_reqs and not any(
                SpecifierSet(r).contains(PYTHON) for r in python_reqs
            ):
                incompatible += 1

            for r in python_reqs:
                for s in SpecifierSet(r):
                    if s.operator in (">=", ">"):
                        minimum = Version(s.version)
                        if highest is None or minimum > highest[0]:
                            highest = (minimum, req.name, version)

        except Exception:
            not_found += 1

print(f"Dependencies checked:             {checked}")
print(f"Not found on PyPI:                 {not_found}")
print(f"Incompatible with Python 3.11:     {incompatible}")
print(
    f"Highest requirement:               {highest[1]}=={highest[2]} (>= {highest[0]})"
    if highest
    else "Highest requirement:               None"
)
