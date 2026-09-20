"""Read and write Saltfile manifests."""

from pathlib import Path

from .saltfile_models import SaltfileConfig
from ..utils.yaml import dump_yaml, load_yaml


def load_saltfile(project_dir: Path | str = Path.cwd()) -> SaltfileConfig:
    return SaltfileConfig(**load_yaml(Path(project_dir) / "Saltfile"))


def save_saltfile(config: SaltfileConfig, project_dir: Path | str = Path.cwd()) -> None:
    dump_yaml(config.model_dump(exclude_none=True), Path(project_dir) / "Saltfile")
