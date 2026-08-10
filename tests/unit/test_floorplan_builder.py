"""Tests for parse-run source binding sanitization (GC-7).

GC-6 (opening width projection) is covered in test_floorplan_normalize.py.
"""

from __future__ import annotations

import hashlib
import io
import types

from PIL import Image, PngImagePlugin

from pwa.files import sha256_file
from pwa.floorplan.builder import _source_binding


def _raw_raster():
    return types.SimpleNamespace(frame=types.SimpleNamespace(kind="raster"), unmapped=())


def _write_jpeg_with_exif(path, *, size: tuple[int, int] = (40, 30), color: str = "red") -> None:
    image = Image.new("RGB", size, color)
    exif = image.getexif()
    exif[0x010F] = "EvilCam Corp"  # Make
    exif[0x9286] = "32.0 N, 34.0 E"  # UserComment stand-in for GPS/author data
    image.save(path, format="JPEG", exif=exif, quality=90)


def _write_png_with_text(path, *, size: tuple[int, int] = (40, 30), color: str = "blue") -> None:
    image = Image.new("RGB", size, color)
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Author", "Secret Person")
    meta.add_text("GPS", "32.0,34.0")
    image.save(path, format="PNG", pnginfo=meta)


def test_source_binding_strips_exif_from_jpeg(tmp_path):
    """GC-7 (PLAN-002 revision 2, 2026-08-10): the raster overlay must embed
    only decoded pixel data, stripped of EXIF and every other metadata
    block -- a JPEG's EXIF (GPS, author, camera model) must never reach
    parse/overlay.svg.
    """
    path = tmp_path / "floorplan.jpg"
    _write_jpeg_with_exif(path)

    binding = _source_binding(path, _raw_raster())

    assert b"EvilCam" not in binding["image_bytes"]
    assert b"32.0 N" not in binding["image_bytes"]
    reopened = Image.open(io.BytesIO(binding["image_bytes"]))
    assert dict(reopened.getexif()) == {}
    assert "exif" not in reopened.info


def test_source_binding_strips_text_chunks_from_png(tmp_path):
    """Same GC-7 requirement, PNG side: ancillary tEXt chunks (author, GPS)
    must not survive sanitization either -- "stripped of EXIF and all other
    metadata blocks" is not JPEG-specific.
    """
    path = tmp_path / "floorplan.png"
    _write_png_with_text(path)

    binding = _source_binding(path, _raw_raster())

    assert b"Secret Person" not in binding["image_bytes"]
    assert b"32.0,34.0" not in binding["image_bytes"]
    reopened = Image.open(io.BytesIO(binding["image_bytes"]))
    assert reopened.info == {}


def test_source_binding_binds_sha256_of_original_not_sanitized_bytes(tmp_path):
    """GC-7: the bound hash must remain the ORIGINAL source file's sha256 --
    never the hash of the sanitized copy, which would break the proof of
    which input produced the overlay.
    """
    path = tmp_path / "floorplan.jpg"
    _write_jpeg_with_exif(path)
    original_hash = sha256_file(path)

    binding = _source_binding(path, _raw_raster())

    sanitized_hash = "sha256:" + hashlib.sha256(binding["image_bytes"]).hexdigest()
    assert binding["source_sha256"] == original_hash
    # Sanitization must actually have changed the bytes (EXIF was present),
    # so this also proves the hash was not silently recomputed from the
    # sanitized copy.
    assert binding["source_sha256"] != sanitized_hash


def test_source_binding_is_byte_deterministic_across_repeated_calls(tmp_path):
    """GC-7: sanitized embedding must be byte-deterministic across repeated
    runs on the same source bytes -- Pillow's encoder settings must be
    pinned.
    """
    path = tmp_path / "floorplan.jpg"
    _write_jpeg_with_exif(path)

    first = _source_binding(path, _raw_raster())
    second = _source_binding(path, _raw_raster())

    assert first["image_bytes"] == second["image_bytes"]


def test_source_binding_png_deterministic_across_repeated_calls(tmp_path):
    path = tmp_path / "floorplan.png"
    _write_png_with_text(path)

    first = _source_binding(path, _raw_raster())
    second = _source_binding(path, _raw_raster())

    assert first["image_bytes"] == second["image_bytes"]


def test_source_binding_preserves_media_type_and_dimensions(tmp_path):
    """Regression guard: sanitization must not regress the existing
    media-type-from-decoded-bytes and width/height behavior.
    """
    jpeg_path = tmp_path / "floorplan.jpg"
    _write_jpeg_with_exif(jpeg_path, size=(64, 48))
    png_path = tmp_path / "floorplan.png"
    _write_png_with_text(png_path, size=(64, 48))

    jpeg_binding = _source_binding(jpeg_path, _raw_raster())
    png_binding = _source_binding(png_path, _raw_raster())

    assert jpeg_binding["media_type"] == "image/jpeg"
    assert png_binding["media_type"] == "image/png"
    assert (jpeg_binding["width_px"], jpeg_binding["height_px"]) == (64, 48)
    assert (png_binding["width_px"], png_binding["height_px"]) == (64, 48)
    assert Image.open(io.BytesIO(jpeg_binding["image_bytes"])).size == (64, 48)
    assert Image.open(io.BytesIO(png_binding["image_bytes"])).size == (64, 48)


def test_source_binding_png_round_trip_is_pixel_perfect(tmp_path):
    """Sanitization re-encodes through Pillow -- for a lossless format this
    must not corrupt or alter the actual pixel data, only strip metadata.
    """
    path = tmp_path / "floorplan.png"
    image = Image.new("RGB", (12, 9))
    for x in range(12):
        for y in range(9):
            image.putpixel((x, y), ((x * 10) % 256, (y * 20) % 256, 128))
    image.save(path, format="PNG")

    binding = _source_binding(path, _raw_raster())

    original = Image.open(path).convert("RGB")
    sanitized = Image.open(io.BytesIO(binding["image_bytes"])).convert("RGB")
    assert list(sanitized.getdata()) == list(original.getdata())
