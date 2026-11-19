#!/usr/bin/env python3
"""Entry point for the news-image-20261119 make.fun bounty (program/v1).

Standard library only: copies the pre-rendered entry.png (drawn by
build_image.py during the build session, with Pillow + numpy) to the
grader's output directory, then verifies the written file before
reporting success. /output in the grader; MAKEFUN_OUTPUT_DIR stands
in for it when run locally:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

Verification (all local, deterministic, no network):
  * bundled entry.png exists and is a fully valid PNG (signature,
    IHDR, per-chunk CRCs, terminating IEND — truncation rejected)
  * image is exactly 1024x1024
  * file is at most 1 MiB (1048576 bytes)
  * the copied file is byte-identical to the bundled entry.png
Any failed check prints a clear error to stderr and exits non-zero.
"""

import hashlib
import os
import shutil
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))

EXPECTED_W, EXPECTED_H = 1024, 1024
MAX_BYTES = 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def check_png(data, label):
    """Validate a PNG fully: signature, IHDR dimensions, then walk every
    chunk checking lengths and CRCs, requiring a terminating IEND chunk
    (so a truncated or corrupted file is rejected). Returns (w, h)."""
    if len(data) < 33:
        fail(f"{label}: too short to be a PNG ({len(data)} bytes)")
    if data[:8] != PNG_SIGNATURE:
        fail(f"{label}: bad PNG signature")
    if data[12:16] != b"IHDR":
        fail(f"{label}: first chunk is not IHDR")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (EXPECTED_W, EXPECTED_H):
        fail(f"{label}: dimensions {width}x{height}, "
             f"expected {EXPECTED_W}x{EXPECTED_H}")
    pos, saw_iend = 8, False
    while pos < len(data):
        if pos + 8 > len(data):
            fail(f"{label}: truncated PNG chunk header")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            fail(f"{label}: truncated "
                 f"{ctype.decode('latin-1')} chunk")
        crc_stored = struct.unpack(">I", data[end - 4:end])[0]
        crc_actual = zlib.crc32(data[pos + 4:end - 4]) & 0xFFFFFFFF
        if crc_stored != crc_actual:
            fail(f"{label}: bad CRC in "
                 f"{ctype.decode('latin-1')} chunk")
        if ctype == b"IEND":
            saw_iend = True
            if end != len(data):
                fail(f"{label}: trailing data after IEND")
            break
        pos = end
    if not saw_iend:
        fail(f"{label}: missing IEND chunk (truncated PNG)")
    return width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    src = os.path.join(HERE, "entry.png")
    dst = os.path.join(out_dir, "entry.png")

    if not os.path.isfile(src):
        fail(f"bundled entry image missing: {src}")

    with open(src, "rb") as fh:
        src_bytes = fh.read()
    check_png(src_bytes, f"bundled {src}")
    if len(src_bytes) > MAX_BYTES:
        fail(f"bundled {src}: {len(src_bytes)} bytes exceeds "
             f"1 MiB limit ({MAX_BYTES})")
    src_digest = hashlib.sha256(src_bytes).hexdigest()

    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, dst)

    with open(dst, "rb") as fh:
        dst_bytes = fh.read()
    check_png(dst_bytes, f"output {dst}")
    if len(dst_bytes) > MAX_BYTES:
        fail(f"output {dst}: {len(dst_bytes)} bytes exceeds "
             f"1 MiB limit ({MAX_BYTES})")
    dst_digest = hashlib.sha256(dst_bytes).hexdigest()
    if dst_bytes != src_bytes:
        fail(f"output {dst} differs from bundled entry.png "
             f"(sha256 {dst_digest[:16]}... != {src_digest[:16]}...)")

    print(f"wrote {dst} ({len(dst_bytes)} bytes, "
          f"{EXPECTED_W}x{EXPECTED_H} PNG, sha256 {dst_digest[:16]}...)")
    print("verified: valid PNG, 1024x1024, <= 1 MiB, "
          "byte-identical to bundled entry.png")


if __name__ == "__main__":
    main()
