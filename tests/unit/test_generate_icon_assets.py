from __future__ import annotations

import struct
from pathlib import Path

import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter

from scripts import generate_icon_assets


def test_ico_variants_are_derived_from_png_without_changing_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(generate_icon_assets, "_asset_root", lambda: tmp_path)
    source = tmp_path / generate_icon_assets.PNG_NAME
    image = QImage(512, 512, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.fillRect(QRect(64, 64, 384, 384), QColor("#75ba38"))
    painter.end()
    assert image.save(str(source), "PNG")
    original_bytes = source.read_bytes()

    assert generate_icon_assets.main() == 0
    assert source.read_bytes() == original_bytes

    ico = (tmp_path / generate_icon_assets.ICO_NAME).read_bytes()
    assert struct.unpack_from("<HHH", ico) == (0, 1, len(generate_icon_assets.ICO_SIZES))
    for index, size in enumerate(generate_icon_assets.ICO_SIZES):
        width, height, _, _, planes, bits, length, offset = struct.unpack_from(
            "<BBBBHHII", ico, 6 + index * 16
        )
        assert (width, height) == ((size, size) if size < 256 else (0, 0))
        assert (planes, bits) == (1, 32)
        variant = QImage.fromData(ico[offset : offset + length], "PNG")
        assert (variant.width(), variant.height()) == (size, size)
        assert variant.pixelColor(0, 0).alpha() < 32
        assert variant.pixelColor(size // 2, size // 2).green() > 0


def test_small_frames_omit_dark_badge_and_fill_more_of_the_icon() -> None:
    source = QImage(512, 512, QImage.Format.Format_ARGB32)
    source.fill(QColor("#19242d"))
    painter = QPainter(source)
    painter.fillRect(QRect(128, 92, 256, 320), QColor("#ed9444"))
    painter.end()

    small = generate_icon_assets._scale_icon(
        generate_icon_assets._small_icon_subject(source), 24
    )
    large = generate_icon_assets._scale_icon(source, 256)

    assert small.pixelColor(0, 0).alpha() == 0
    assert small.pixelColor(12, 12).red() > 200
    assert large.pixelColor(0, 0).alpha() == 255


def test_invalid_png_source_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "invalid.png"
    source.write_bytes(b"not a png")

    with pytest.raises(RuntimeError, match="Invalid PNG icon source"):
        generate_icon_assets._load_png_source(source)
