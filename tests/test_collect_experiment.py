from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "cluster" / "collect-experiment.py"
SPEC = spec_from_file_location("collect_experiment", SCRIPT)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_parse_duration() -> None:
    assert MODULE.parse_duration("00:16:40") == 1000
    assert MODULE.parse_duration("1-01:02:03") == 90123
    assert MODULE.parse_duration("57:30.093") == 3450.093


def test_parse_memory_mib() -> None:
    assert MODULE.parse_memory_mib("4336680K") == 4336680 / 1024
    assert MODULE.parse_memory_mib("32G") == 32768


def test_parse_sacct_requires_training_steps() -> None:
    output = "\n".join(
        (
            "JobID|JobName",
            "20755|polysight-train",
            "20755.batch|batch",
            "20755.0|polysight-train",
        )
    )
    rows = MODULE.parse_sacct(output, "20755")
    assert rows["20755.0"]["JobName"] == "polysight-train"
