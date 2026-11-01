"""TC-01-04: 版本常量与规格给定值逐字一致 (m25 TECHNICAL.md "版本常量";
m25 D013/D016).

任何一边改了都要同时改另一边并重看规格, 防止版本漂移与转抄错.
"""
from __future__ import annotations

import pytest

from codemap_helpers import codemap_common as cmc


@pytest.mark.parametrize(
    "name, expected",
    [
        ("IMAGE_TAG", "docker.io/codecharta/codecharta-analysis:2.3.0"),
        ("IMAGE_SINGLE_ARCH_DIGEST",
         "sha256:286b0a54f947c412b7c290a57312ac2c4327352531e046ad4ab834c13b2ddc36"),
        ("IMAGE_MULTI_ARCH_DIGEST",
         "sha256:6402a87f6823c8123de6c8706ffc7b68ae75ce2c2c58aa8b3fcab59e97d1f7a4"),
        ("FRONTEND_VERSION", "vis-2.9.1"),
        ("FRONTEND_ZIP_SHA256",
         "18b6377f9f482c3e34dd9a3ab8a716d6a7171ad68fa2d6670a516761b0be3682"),
        ("DEFAULT_PORT", 8090),
        ("BIND", "0.0.0.0"),
    ],
    ids=["image_tag", "single_arch_digest", "multi_arch_digest",
         "frontend_version", "frontend_zip_sha256", "default_port", "bind"],
)
def test_version_constant_matches_spec_verbatim(name, expected):
    assert getattr(cmc, name) == expected
