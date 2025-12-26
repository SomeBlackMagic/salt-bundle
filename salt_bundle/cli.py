"""CLI interface for salt-bundle - main entry point.

This module imports and exposes the CLI from the modular structure.
All commands are now organized in the cli/ subdirectory.
"""

import sys
from pathlib import Path

# Handle both package import and direct execution
try:
    from .cli import main
except ImportError:
    # Direct execution - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from salt_bundle.cli import main


if __name__ == '__main__':
    main()
