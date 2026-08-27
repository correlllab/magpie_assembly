#!/usr/bin/env python3
"""Cut the figures out of `Documentation/Magpie Assembly Guide.pdf`.

The assembly guide is written as a PDF, but a builder reading it on GitHub
should not have to download one — `Documentation/assembly.md` is the same guide
in Markdown, and it uses these figures.  Pulling them from the PDF rather than
re-picking them by hand keeps the two versions showing the same pictures:
re-export the guide, re-run this, and the Markdown follows.

    python3 -m pip install pymupdf pillow
    python3 tools/extract_guide_figures.py

Full-resolution originals of every build photo (including the ones the guide
did not use) live in Documentation/assembly_photos/.
"""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
PDF = REPO / "Documentation" / "Magpie Assembly Guide.pdf"
OUT = REPO / "Documentation" / "figures"

# (1-based page, index within the page) -> file name.  Where a step has two
# figures side by side, the left one comes first — the index order the PDF
# reports happens to match, and `verify_layout` below fails if it stops doing so.
FIGURES = {
    (2, 0): "00-parts-laid-out",
    (3, 0): "02-servos-from-below",
    (3, 1): "02-servos-edge-on",
    (4, 0): "03-linkage-parts",
    (4, 1): "03-finger-subassembly",
    (5, 0): "04-crank-on-horn",
    (5, 1): "05-both-linkages",
    (6, 0): "06-top-base-joined",
    (6, 1): "06-top-base-edge-on",
    (6, 2): "07-camera-installed-1",
    (6, 3): "07-camera-installed-2",
    (7, 0): "08-openrb-installed",
    (7, 1): "09-protector-fitted",
    (7, 2): "09-protector-detail",
    (8, 0): "10-wiring-from-above",
    (8, 1): "10-wiring-underside",
    (9, 0): "10-wiring-detail-1",
    (9, 1): "10-wiring-detail-2",
}


def verify_layout(page: pymupdf.Page, xrefs: list[int]) -> None:
    """Fail loudly if the figures on a page are no longer in reading order."""
    boxes = []
    for xref in xrefs:
        rects = page.get_image_rects(xref)
        if rects:
            boxes.append((round(rects[0].y0 / 40), rects[0].x0))
    if boxes != sorted(boxes):
        raise SystemExit(
            f"page {page.number + 1}: figures are no longer in reading order — "
            "check the FIGURES table against the PDF before trusting the output"
        )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    written = 0
    for pno in range(len(doc)):
        page = doc[pno]
        xrefs = [im[0] for im in page.get_images(full=True)]
        if not xrefs:
            continue
        verify_layout(page, xrefs)
        for index, xref in enumerate(xrefs):
            name = FIGURES.get((pno + 1, index))
            if name is None:
                print(f"page {pno + 1} figure {index}: not in the table, skipped")
                continue
            data = doc.extract_image(xref)
            img = Image.open(io.BytesIO(data["image"])).convert("RGB")
            path = OUT / f"{name}.jpg"
            img.save(path, quality=88, optimize=True, progressive=True)
            print(f"{path.relative_to(REPO)}  {img.width}×{img.height}  {path.stat().st_size // 1024} KB")
            written += 1
    missing = set(FIGURES.values()) - {p.stem for p in OUT.glob("*.jpg")}
    if missing:
        raise SystemExit(f"expected figures never appeared: {sorted(missing)}")
    print(f"{written} figures")


if __name__ == "__main__":
    main()
