"""Document API."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.document_service import DocumentNotFoundError, DocumentService
from app.hwpx.validator import detect_inconsistent_numbers, validate_hwpx_package, validate_table_sums


router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "upload.hwpx").suffix or ".hwpx"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)
    try:
        document = DocumentService().upload_from_path(temp_path, file.filename)
        return document.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)


@router.get("")
def list_documents() -> list[dict]:
    return DocumentService().list_documents()


@router.get("/{document_id}")
def get_document(document_id: str) -> dict:
    try:
        return DocumentService().load_document(document_id).model_dump(mode="json")
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.get("/{document_id}/outline")
def get_outline(document_id: str) -> dict:
    document = DocumentService().load_document(document_id)
    return {
        "document_id": document.id,
        "sections": [
            {
                "id": section.id,
                "order": section.order,
                "paragraph_count": len(section.paragraphs),
                "table_count": len(section.tables),
            }
            for section in document.sections
        ],
    }


@router.get("/{document_id}/tables")
def get_tables(document_id: str) -> list[dict]:
    return [table.model_dump(mode="json") for table in DocumentService().load_document(document_id).tables]


@router.post("/{document_id}/search")
def search_text(document_id: str, request: SearchRequest) -> list[dict]:
    document = DocumentService().load_document(document_id)
    return [
        {"paragraph_id": paragraph.id, "text": paragraph.text, "source_xml_path": paragraph.source_xml_path}
        for paragraph in document.paragraphs
        if request.query in paragraph.text
    ]


@router.post("/{document_id}/validate")
def validate_document(document_id: str) -> dict:
    service = DocumentService()
    row = service.document_row(document_id)
    document = service.load_document(document_id)
    return {
        "package": validate_hwpx_package(Path(row["original_path"])),
        "table_sums": [issue for table in document.tables for issue in validate_table_sums(table)],
        "inconsistent_numbers": detect_inconsistent_numbers(document),
    }


@router.get("/{document_id}/download")
def download_document(document_id: str) -> FileResponse:
    row = DocumentService().document_row(document_id)
    path = Path(row["output_path"] or row["original_path"])
    return FileResponse(path, filename=path.name)

