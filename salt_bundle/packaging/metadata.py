"""Read and write FORMULA and EXTENSION metadata files."""

from pathlib import Path

from .extensions import ExtensionMeta
from .models import PackageMeta
from .types import load_package_meta as load_detected_package_meta
from ..utils.yaml import dump_yaml, load_yaml


def load_formula_meta(package_dir: Path | str = Path.cwd()) -> PackageMeta:
    return PackageMeta(**load_yaml(Path(package_dir) / "FORMULA"))


def save_formula_meta(meta: PackageMeta, package_dir: Path | str = Path.cwd()) -> None:
    dump_yaml(meta.model_dump(exclude_none=True), Path(package_dir) / "FORMULA")


def load_extension_meta(package_dir: Path | str = Path.cwd()) -> ExtensionMeta:
    return ExtensionMeta(**load_yaml(Path(package_dir) / "EXTENSION"))


def save_extension_meta(meta: ExtensionMeta, package_dir: Path | str = Path.cwd()) -> None:
    dump_yaml(meta.model_dump(exclude_none=True), Path(package_dir) / "EXTENSION")


def load_package_meta(package_dir: Path | str = Path.cwd()) -> PackageMeta | ExtensionMeta:
    return load_detected_package_meta(package_dir)
