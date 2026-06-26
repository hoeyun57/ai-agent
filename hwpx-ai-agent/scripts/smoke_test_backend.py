"""Dependency-light backend smoke test for environments without pytest."""

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
import asyncio
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.agents.planner import Planner
from app.hwpx.package import HwpxPackage
from app.hwpx.parser import HwpxParseError, parse_document
from app.hwpx.table_editor import update_table_cell
from app.hwpx.text_editor import replace_text
from app.hwpx.validator import validate_hwpx_package, validate_table_sums
from app.security.zip_security import ZipSecurityError, safe_extract
from app.tools.number_tools import parse_number


SECTION_XML = """<?xml version="1.0" encoding="UTF-8"?>
<section>
  <p><t>2025년 사업 계획입니다. 총 예산은 60,000원입니다.</t></p>
  <tbl>
    <tr><tc><p><t>항목A</t></p></tc><tc><p><t>10,000원</t></p></tc><tc><p><t>20,000원</t></p></tc><tc><p><t>30,000원</t></p></tc></tr>
    <tr><tc><p><t>항목B</t></p></tc><tc><p><t>30,000원</t></p></tc><tc><p><t>35,000원</t></p></tc><tc><p><t>60,000원</t></p></tc></tr>
  </tbl>
</section>
"""


def make_hwpx(path: Path, xml: str = SECTION_XML) -> None:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/hwp+zip")
        archive.writestr("Contents/section0.xml", xml)


async def main() -> None:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.hwpx"
        make_hwpx(sample)
        workspace = tmp_path / "workspace"
        package = HwpxPackage.open(sample, workspace, 100, 10_000_000)
        document = parse_document("doc-test", "sample.hwpx", workspace)
        assert "2025년" in document.paragraphs[0].text
        assert document.tables and document.tables[0].rows == 2
        assert parse_number("1억원") and str(parse_number("1억원").value) == "100000000"
        assert validate_table_sums(document.tables[0])[0]["calculated_total"] == "65000"
        assert update_table_cell(workspace, "table-1-1", 1, 2, "15,000원")["before"] == "10,000원"
        assert replace_text(workspace, "2025년", "2026년")
        output = tmp_path / "out.hwpx"
        package.repack(output)
        assert validate_hwpx_package(output)["valid"] is True
        plan = await Planner().create_plan("2025년을 모두 2026년으로 변경해줘", document)
        assert plan.requires_approval is True
        bad = tmp_path / "bad.hwpx"
        with ZipFile(bad, "w") as archive:
            archive.writestr("../evil.xml", "<section/>")
        try:
            safe_extract(bad, tmp_path / "bad-out", 100, 10_000)
            raise AssertionError("ZIP Slip was not blocked")
        except ZipSecurityError:
            pass
        xxe = tmp_path / "xxe.hwpx"
        make_hwpx(xxe, "<!DOCTYPE foo [ <!ENTITY xxe SYSTEM 'file:///etc/passwd'> ]><section>&xxe;</section>")
        xxe_workspace = tmp_path / "xxe-workspace"
        HwpxPackage.open(xxe, xxe_workspace, 100, 10_000_000)
        try:
            parse_document("doc-xxe", "xxe.hwpx", xxe_workspace)
            raise AssertionError("XXE was not blocked")
        except HwpxParseError:
            pass
    print("backend smoke tests passed")


if __name__ == "__main__":
    asyncio.run(main())

