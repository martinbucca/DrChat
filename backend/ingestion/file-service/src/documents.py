import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from fastapi.responses import JSONResponse



router = APIRouter()

@router.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"{file.filename} no es un archivo PDF")

        storage_folder = "/app/storage"
        os.makedirs(storage_folder, exist_ok=True)        
        file_location = os.path.join(storage_folder, file.filename)
        
        print(file_location)
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
        
        saved_files.append({"filename": file.filename, "path": file_location})

    return JSONResponse(content={"message": "Files uploaded successfully."})
