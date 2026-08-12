"""Constantes verificadas del archivo etiquetado de HyperKvasir."""

ARCHIVE_SIZE_BYTES = 3_928_814_344
ARCHIVE_SHA256 = "c603449b1bc0be86948b11d9aea8b2002058a11e6f5499e2a384b9ae9c8dbd3f"
EXPECTED_IMAGE_COUNT = 10_662
EXPECTED_CLASS_COUNT = 23
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}

SPLIT_RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}
DEFAULT_SEED = 42
MAIN_CLASS_MIN_IMAGES = 100
