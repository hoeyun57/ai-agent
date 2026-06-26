from pathlib import Path

import pytest
from zipfile import ZipFile

from app.hwpx.package import HwpxPackage
from app.hwpx.parser import HwpxParseError, parse_document
from app.hwpx.table_editor import update_table_cell
from app.hwpx.text_editor import replace_text
from app.hwpx.validator import validate_hwpx_package, validate_table_sums
from app.security.zip_security import ZipSecurityError, safe_extract
from app.tools.number_tools import parse_number


def test_parse_hwpx_text_and_tables(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    document = parse_document("doc-test", "sample.hwpx", workspace)
    assert "2025년" in document.paragraphs[0].text
    assert document.tables[0].rows == 2
    assert document.tables[0].cells[1].numeric_value is not None


def test_zip_slip_blocked(tmp_path: Path) -> None:
    bad = tmp_path / "bad.hwpx"
    from zipfile import ZipFile

    with ZipFile(bad, "w") as archive:
        archive.writestr("../evil.xml", "<section/>")
    with pytest.raises(ZipSecurityError):
        safe_extract(bad, tmp_path / "out", 100, 10_000)


def test_xxe_blocked(xxe_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(xxe_hwpx, workspace, 100, 10_000_000)
    with pytest.raises(HwpxParseError):
        parse_document("doc-test", "xxe.hwpx", workspace)


def test_replace_text_preserves_original_and_creates_valid_output(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    package = HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    changes = replace_text(workspace, "2025년", "2026년")
    output = tmp_path / "out.hwpx"
    package.repack(output)
    assert changes
    with ZipFile(sample_hwpx) as archive:
        assert "2025년" in archive.read("Contents/section0.xml").decode("utf-8")
    assert validate_hwpx_package(output)["valid"] is True


def test_update_table_cell(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    change = update_table_cell(workspace, "table-1-1", 1, 2, "15,000원")
    assert change["before"] == "10,000원"
    document = parse_document("doc-test", "sample.hwpx", workspace)
    assert document.tables[0].cells[1].text == "15,000원"


def test_table_sum_mismatch(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    document = parse_document("doc-test", "sample.hwpx", workspace)
    issues = validate_table_sums(document.tables[0])
    assert issues[0]["status"] == "mismatch"
    assert issues[0]["calculated_total"] == "65000"


@pytest.mark.parametrize(
    ("raw", "value"),
    [("1,000", "1000"), ("1000원", "1000"), ("10만원", "100000"), ("1억원", "100000000"), ("3.5%", "3.5")],
)
def test_number_unit_conversion(raw: str, value: str) -> None:
    parsed = parse_number(raw)
    assert parsed is not None
    assert str(parsed.value) == value
