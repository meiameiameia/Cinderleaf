from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage


PNG_NAME = "app-icon.png"
ICO_NAME = "cinderleaf.ico"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
SMALL_ICON_SIZES = (16, 24, 32, 48)


def _asset_root() -> Path:
    return Path(__file__).resolve().parents[1] / "assets"


def _load_png_source(png_path: Path) -> QImage:
    image = QImage(str(png_path))
    if image.isNull():
        raise RuntimeError(f"Invalid PNG icon source: {png_path}")
    if image.width() != image.height() or image.width() < max(ICO_SIZES):
        raise RuntimeError("PNG icon source must be square and at least 256 pixels")
    if not image.hasAlphaChannel():
        raise RuntimeError("PNG icon source must have a transparent exterior")
    return image


def _scale_icon(image: QImage, size: int) -> QImage:
    return image.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _small_icon_subject(image: QImage) -> QImage:
    """Keep the sprout and crate legible where the full badge becomes tiny."""
    subject = QImage(image.size(), QImage.Format.Format_ARGB32)
    subject.fill(Qt.GlobalColor.transparent)
    left, top = image.width(), image.height()
    right = bottom = -1
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            hue, saturation, value, _ = color.getHsv()
            if not (0 <= hue <= 160 and saturation >= 130 and value >= 65):
                continue
            coverage = min(255, (saturation - 120) * 14, (value - 55) * 10)
            color.setAlpha(color.alpha() * coverage // 255)
            subject.setPixelColor(x, y, color)
            if color.alpha() > 32:
                left, top = min(left, x), min(top, y)
                right, bottom = max(right, x), max(bottom, y)
    if right < left or bottom < top:
        raise RuntimeError("PNG icon source has no visible sprout-and-crate subject")

    width, height = right - left + 1, bottom - top + 1
    side = min(min(image.width(), image.height()), round(max(width, height) * 1.10))
    x = max(0, left - (side - width) // 2)
    y = max(0, top - (side - height) // 2)
    x = min(x, image.width() - side)
    y = min(y, image.height() - side)
    return subject.copy(x, y, side, side)


def _image_to_png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise RuntimeError("Unable to open in-memory PNG buffer")
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Unable to encode PNG image")
    buffer.close()
    return bytes(data)


def _write_ico(ico_path: Path, images: list[tuple[int, bytes]]) -> None:
    # ICO stores PNG blobs directly so the approved PNG controls every size.
    header = struct.pack("<HHH", 0, 1, len(images))
    entries: list[bytes] = []
    offset = 6 + 16 * len(images)
    for size, blob in images:
        width = size if size < 256 else 0
        height = size if size < 256 else 0
        entries.append(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(blob),
                offset,
            )
        )
        offset += len(blob)

    with ico_path.open("wb") as handle:
        handle.write(header)
        for entry in entries:
            handle.write(entry)
        for _, blob in images:
            handle.write(blob)


def main() -> int:
    asset_root = _asset_root()
    png_path = asset_root / PNG_NAME
    ico_path = asset_root / ICO_NAME

    if not png_path.is_file():
        raise FileNotFoundError(f"PNG source not found: {png_path}")
    png_image = _load_png_source(png_path)
    small_subject = _small_icon_subject(png_image)

    ico_images: list[tuple[int, bytes]] = []
    for size in ICO_SIZES:
        image = _scale_icon(small_subject if size in SMALL_ICON_SIZES else png_image, size)
        ico_images.append((size, _image_to_png_bytes(image)))
    _write_ico(ico_path, ico_images)

    print(png_path)
    print(ico_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
