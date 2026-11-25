#!/usr/bin/env python3
"""Copy the one-line review to the make.fun output directory.

Reads entry.txt beside this script, checks it against the gate (valid UTF-8,
1-200 characters, not only whitespace), then writes those exact bytes to
$MAKEFUN_OUTPUT_DIR/entry.txt (default /output), creating the directory if
needed, and confirms the copy by sha256.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

MIN_CHARS = 1
MAX_CHARS = 200
SOURCE_NAME = "entry.txt"
OUTPUT_NAME = "entry.txt"


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    return 1


def read_source(path):
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SystemExit(fail(f"cannot read {path}: {exc}"))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(fail(f"{path} is not valid UTF-8: {exc}"))
    count = len(text)
    if not (MIN_CHARS <= count <= MAX_CHARS):
        raise SystemExit(
            fail(f"{path} must be {MIN_CHARS}-{MAX_CHARS} characters, got {count}")
        )
    if not text.strip():
        raise SystemExit(fail(f"{path} is only whitespace"))
    return raw


def destination_dir():
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def main():
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    raw = read_source(source)

    out_dir = destination_dir()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SystemExit(fail(f"cannot create {out_dir}: {exc}"))

    dest = out_dir / OUTPUT_NAME
    try:
        shutil.copyfile(source, dest)
    except shutil.SameFileError:
        raise SystemExit(
            fail(f"refusing to copy {source} onto itself (SameFileError)")
        )
    except OSError as exc:
        raise SystemExit(fail(f"cannot write {dest}: {exc}"))

    source_digest = hashlib.sha256(raw).hexdigest()
    try:
        written = dest.read_bytes()
    except OSError as exc:
        raise SystemExit(fail(f"cannot read back {dest}: {exc}"))

    written_digest = hashlib.sha256(written).hexdigest()
    if written_digest != source_digest or written != raw:
        raise SystemExit(
            fail(
                "sha256 mismatch after copy: "
                f"source {source_digest}, destination {written_digest}"
            )
        )

    chars = len(written.decode("utf-8"))
    print(
        f"wrote {dest} ({chars} characters, {len(written)} bytes, "
        f"sha256 {written_digest})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
