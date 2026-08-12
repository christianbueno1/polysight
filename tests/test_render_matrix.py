from __future__ import annotations

from pathlib import Path

from PIL import Image

from polysight.render_matrix import main


def test_render_matrix_cli_uses_readable_default_name(tmp_path: Path) -> None:
    input_path = tmp_path / "confusion-matrix.csv"
    input_path.write_text("actual\\predicted,a,b\na,8,2\nb,1,9\n", encoding="utf-8")

    assert main(["--input", str(input_path)]) == 0

    output = tmp_path / "confusion-matrix-normalized-readable.png"
    assert output.is_file()
    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.width >= 1800
        assert image.height >= 1800
