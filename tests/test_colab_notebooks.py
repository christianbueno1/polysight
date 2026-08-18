import ast
import json
from pathlib import Path

NOTEBOOK_DIR = Path(__file__).parents[1] / "notebooks"
EXPECTED_NOTEBOOKS = {
    "01-polysight-inference-verification.ipynb",
    "02-polysight-training-reproduction.ipynb",
}


def load_notebook(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def notebook_text(notebook: dict[str, object]) -> str:
    cells = notebook["cells"]
    assert isinstance(cells, list)
    return "\n".join("".join(cell["source"]) for cell in cells)


def test_colab_notebooks_are_valid_and_without_saved_outputs() -> None:
    paths = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    assert {path.name for path in paths} == EXPECTED_NOTEBOOKS
    for path in paths:
        notebook = load_notebook(path)
        assert notebook["nbformat"] == 4
        cells = notebook["cells"]
        assert isinstance(cells, list) and cells
        for index, cell in enumerate(cells):
            if cell["cell_type"] != "code":
                continue
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
            ast.parse("".join(cell["source"]), filename=f"{path}:cell-{index}")


def test_inference_notebook_verifies_the_audited_checkpoint() -> None:
    notebook = load_notebook(NOTEBOOK_DIR / "01-polysight-inference-verification.ipynb")
    text = notebook_text(notebook)
    assert "74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c" in text
    assert "from polysight.predict import predict" in text
    assert "files.upload()" in text


def test_training_notebook_preserves_the_reproduction_contract() -> None:
    notebook = load_notebook(NOTEBOOK_DIR / "02-polysight-training-reproduction.ipynb")
    text = notebook_text(notebook)
    assert "87ac0694dc8e53f6d295b902ce4465af8dfd2aff" in text
    assert "c603449b1bc0be86948b11d9aea8b2002058a11e6f5499e2a384b9ae9c8dbd3f" in text
    assert "8f59d5c5f1d188ad75d1b28c6ab9b56e3b3c68bcf8f7dd0940422dc8df27f463" in text
    assert "74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c" in text
    assert '"pytest", "-q"' in text
    assert '"ruff", "check", "."' in text
    assert "inspect.getsource(symbol)" in text
    assert "from polysight.predict import predict" in text
    assert "configs/smoke-main16.yaml" in text
    assert "configs/main16-baseline.yaml" in text
    assert 'RUN_TEST_EVALUATION = False' in text
    assert '"--seed", "42"' in text
