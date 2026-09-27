"""Tests for runtime backend errors."""

import importlib.util
import unittest


class TestBackendErrors(unittest.TestCase):
    """Specify backend error classes as independent public errors."""

    def test_backend_errors_are_instantiable(self) -> None:
        spec = importlib.util.find_spec("salt_bundle.runtime.errors")
        self.assertIsNotNone(spec, "runtime must provide an errors module")

        from salt_bundle.runtime import errors

        preparation_error = errors.BackendPreparationError("Unable to build runtime")
        execution_error = errors.BackendExecutionError("Salt command failed")

        self.assertIsInstance(preparation_error, Exception)
        self.assertIsInstance(execution_error, Exception)
        self.assertEqual(str(preparation_error), "Unable to build runtime")
        self.assertEqual(str(execution_error), "Salt command failed")
