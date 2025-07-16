from backend.app.services.document_parser import extract_text_from_pdf
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()

@router.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"{file.filename} no es un archivo PDF")
        
        contents = await file.read()
        text = extract_text_from_pdf(contents)
        results.append({
        "filename": file.filename,
        "text": text
        })


    return {"processed": results}
