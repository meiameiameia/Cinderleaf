from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import prepare_qt_sources


def test_fetch_verified_source_reuses_matching_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "qtbase.tar.xz"
    archive.write_bytes(b"known source")
    expected = hashlib.sha256(archive.read_bytes()).hexdigest()

    def unexpected_download(*args: object, **kwargs: object) -> None:
        raise AssertionError("matching source should not be downloaded again")

    monkeypatch.setattr(prepare_qt_sources, "urlopen", unexpected_download)

    assert (
        prepare_qt_sources._fetch_verified(
            archive.name, "https://example.invalid/source", expected, tmp_path
        )
        == archive
    )


def test_fetch_verified_source_rejects_wrong_hash(tmp_path: Path) -> None:
    source = tmp_path / "source.tar.xz"
    source.write_bytes(b"wrong source")
    target = tmp_path / "download"

    with pytest.raises(RuntimeError, match="source hash mismatch"):
        prepare_qt_sources._fetch_verified(
            "source.tar.xz", source.as_uri(), "0" * 64, target
        )

    assert not (target / "source.tar.xz").exists()
    assert not (target / "source.tar.xz.part").exists()
