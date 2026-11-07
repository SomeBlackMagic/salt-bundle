"""Tests for Salt master_tops integration."""

from salt_bundle.salt._tops import salt_bundle


def test_top_adds_matching_formula_and_ignores_extension(tmp_path):
    formula = tmp_path / "vendor" / "example" / "foo-formula"
    formula.mkdir(parents=True)
    (formula / "foo").mkdir()
    (formula / "foo" / "init.sls").write_text("foo: {}\n")
    (formula / "FORMULA").write_text(
        "name: example/foo-formula\nversion: 1.0.0\ntop_level_dir: foo\n"
    )
    extension = tmp_path / "vendor" / "example" / "helper"
    extension.mkdir(parents=True)
    (extension / "EXTENSION").write_text("name: example/helper\nversion: 1.0.0\n")
    (tmp_path / "Saltfile").write_text(
        "vendor_dir: vendor\nruntime:\n  top_bundle_file: salt/top_bundle.sls\n"
    )
    (tmp_path / "Saltfile.lock").write_text(
        "dependencies:\n"
        "  example/foo-formula:\n"
        "    version: 1.0.0\n    repository: local\n    url: local\n"
        "    digest: linked\n    type: formula\n"
        "  example/helper:\n"
        "    version: 1.0.0\n    repository: local\n    url: local\n"
        "    digest: linked\n    type: extension\n"
    )
    top_file = tmp_path / "salt" / "top_bundle.sls"
    top_file.parent.mkdir()
    top_file.write_text(
        "base:\n  'web-*':\n    - example/foo-formula\n    - example/helper\n"
    )

    assert salt_bundle.top(opts={"id": "web-01", "config_dir": str(tmp_path)}) == {
        "base": ["foo"]
    }
    assert salt_bundle.top(opts={"id": "db-01", "config_dir": str(tmp_path)}) == {}
