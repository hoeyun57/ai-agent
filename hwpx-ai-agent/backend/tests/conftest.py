from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest


SECTION_XML = """<?xml version="1.0" encoding="UTF-8"?>
<section>
  <p><t>2025년 사업 계획입니다. 총 예산은 60,000원입니다.</t></p>
  <tbl>
    <tr><tc><p><t>항목A</t></p></tc><tc><p><t>10,000원</t></p></tc><tc><p><t>20,000원</t></p></tc><tc><p><t>30,000원</t></p></tc></tr>
    <tr><tc><p><t>항목B</t></p></tc><tc><p><t>30,000원</t></p></tc><tc><p><t>35,000원</t></p></tc><tc><p><t>60,000원</t></p></tc></tr>
  </tbl>
</section>
"""


@pytest.fixture()
def sample_hwpx(tmp_path: Path) -> Path:
    path = tmp_path / "sample.hwpx"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/hwp+zip")
        archive.writestr("Contents/section0.xml", SECTION_XML)
    return path


@pytest.fixture()
def xxe_hwpx(tmp_path: Path) -> Path:
    path = tmp_path / "xxe.hwpx"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("Contents/section0.xml", "<!DOCTYPE foo [ <!ENTITY xxe SYSTEM 'file:///etc/passwd'> ]><section>&xxe;</section>")
    return path

