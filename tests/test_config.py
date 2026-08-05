from pathlib import Path

import pytest

from polysight.config import load_config


def test_load_config_expands_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLYSIGHT_DATA_DIR", "/dataset")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
name: test
profile: main16
data:
  data_dir: ${POLYSIGHT_DATA_DIR}
  manifest: /manifests/main16/manifest.csv
training:
  loss: weighted_cross_entropy
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.data.data_dir == "/dataset"
    assert config.training.loss == "weighted_cross_entropy"
    assert config.model.architecture == "efficientnet_b0"


def test_rejects_unknown_loss(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
name: test
profile: main16
data:
  data_dir: /dataset
  manifest: /manifest.csv
training:
  loss: invented
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Pérdida inválida"):
        load_config(config_path)
