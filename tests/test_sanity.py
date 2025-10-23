from __future__ import annotations

import re
import algoviz


def test_version_format():
    assert re.match(r"^\d+\.\d+\.\d+(?:[ab]\d+)?$", algoviz.__version__), algoviz.__version__


def test_import_packages():
    # 确保包结构正确
    import algoviz.core  # noqa: F401
    import algoviz.backends  # noqa: F401
    import algoviz.components  # noqa: F401
