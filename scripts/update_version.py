"""Update version_file.txt and app/version.py before building EXE.
Usage: python scripts/update_version.py 1.2.3
"""
import sys
import re

def update_version_file(version: str):
    parts = version.split(".")
    if len(parts) != 3:
        print(f"Error: expected X.Y.Z format, got '{version}'")
        sys.exit(1)

    major, minor, patch = parts
    ver_tuple = f"({major}, {minor}, {patch}, 0)"
    ver_str   = f"{version}.0"

    path = "version_file.txt"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r"filevers=\([^)]+\)", f"filevers={ver_tuple}", content)
    content = re.sub(r"prodvers=\([^)]+\)", f"prodvers={ver_tuple}", content)
    content = re.sub(r"(u'FileVersion',\s+u')[^']+(')", rf"\g<1>{ver_str}\g<2>", content)
    content = re.sub(r"(u'ProductVersion',\s+u')[^']+(')", rf"\g<1>{ver_str}\g<2>", content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"version_file.txt updated to {version}")

    vpath = "app/version.py"
    with open(vpath, "r", encoding="utf-8") as f:
        vc = f.read()
    vc = re.sub(r'VERSION\s*=\s*"[^"]+"', f'VERSION     = "{version}"', vc)
    with open(vpath, "w", encoding="utf-8") as f:
        f.write(vc)
    print(f"app/version.py updated to {version}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py 1.2.3")
        sys.exit(1)
    update_version_file(sys.argv[1])
