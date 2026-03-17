from fastapi import APIRouter, Body, File, UploadFile, HTTPException
import os
import traceback
from typing import Annotated, List, Optional

from constants.documents import UPLOAD_ACCEPTED_FILE_TYPES
from models.decomposed_file_info import DecomposedFileInfo
from services.temp_file_service import TEMP_FILE_SERVICE
from services.documents_loader import DocumentsLoader
import uuid
from utils.validators import validate_files

FILES_ROUTER = APIRouter(prefix="/files", tags=["Files"])


@FILES_ROUTER.post("/upload", response_model=List[str])
async def upload_files(files: Optional[List[UploadFile]]):
    try:
        print(f"DEBUG: Upload endpoint hit. Files received: {files}")
        if not files:
            print("DEBUG: No files provided.")
            raise HTTPException(400, "Documents are required")

        print("DEBUG: Creating temp directory...")
        temp_dir = TEMP_FILE_SERVICE.create_temp_dir(str(uuid.uuid4()))
        print(f"DEBUG: Temp directory created at: {temp_dir}")

        print("DEBUG: Validating files...")
        try:
            validate_files(files, True, True, 100, UPLOAD_ACCEPTED_FILE_TYPES)
            print("DEBUG: Files validated successfully.")
        except Exception as ve:
            print(f"DEBUG: Validation failed: {ve}")
            raise ve

        temp_files: List[str] = []
        if files:
            for each_file in files:
                print(f"DEBUG: Processing file: {each_file.filename}")
                temp_path = TEMP_FILE_SERVICE.create_temp_file_path(
                    each_file.filename, temp_dir
                )
                print(f"DEBUG: Writing to temp path: {temp_path}")
                # Use chunks to write file to avoid memory issues with large files
                with open(temp_path, "wb") as f:
                    while content := await each_file.read(1024 * 1024):  # Read in 1MB chunks
                        f.write(content)
                print(f"DEBUG: File written successfully: {temp_path}")
                temp_files.append(temp_path)

        return temp_files
    except HTTPException as he:
        print(f"DEBUG: HTTPException caught: {he.detail}")
        raise he
    except Exception as e:
        print("ERROR: Exception in upload_files:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@FILES_ROUTER.post("/decompose", response_model=List[DecomposedFileInfo])
async def decompose_files(file_paths: Annotated[List[str], Body(embed=True)]):
    try:
        print(f"DEBUG: Decompose endpoint hit. File paths received: {file_paths}")
        
        print("DEBUG: Creating temp directory for decomposition...")
        temp_dir = TEMP_FILE_SERVICE.create_temp_dir(str(uuid.uuid4()))
        print(f"DEBUG: Temp directory created at: {temp_dir}")

        txt_files = []
        other_files = []
        for file_path in file_paths:
            print(f"DEBUG: Checking file path: {file_path}")
            if file_path.endswith(".txt"):
                txt_files.append(file_path)
            else:
                other_files.append(file_path)
        
        print(f"DEBUG: Found {len(txt_files)} text files and {len(other_files)} other files.")

        parsed_documents = []
        if other_files:
            print(f"DEBUG: Initializing DocumentsLoader for {other_files}")
            documents_loader = DocumentsLoader(file_paths=other_files)
            print("DEBUG: Loading documents...")
            try:
                await documents_loader.load_documents(temp_dir)
                parsed_documents = documents_loader.documents
                print(f"DEBUG: Successfully parsed {len(parsed_documents)} documents.")
            except Exception as load_err:
                print(f"ERROR: Failed to load documents: {load_err}")
                traceback.print_exc()
                raise load_err

        response = []
        for index, parsed_doc in enumerate(parsed_documents):
            try:
                original_file = other_files[index]
                print(f"DEBUG: Processing parsed content for {original_file}")
                
                new_file_name = f"{uuid.uuid4()}.txt"
                file_path = TEMP_FILE_SERVICE.create_temp_file_path(
                    new_file_name, temp_dir
                )
                
                # Replace <br> with newline
                parsed_doc = parsed_doc.replace("<br>", "\n")
                
                print(f"DEBUG: Writing decomposed content to {file_path}")
                with open(file_path, "w", encoding="utf-8") as text_file:
                    text_file.write(parsed_doc)
                
                response.append(
                    DecomposedFileInfo(
                        name=os.path.basename(original_file), file_path=file_path
                    )
                )
            except Exception as write_err:
                 print(f"ERROR: Failed to write parsed document index {index}: {write_err}")
                 traceback.print_exc()
                 raise write_err

        # Return the txt documents as it is
        for each_file in txt_files:
            print(f"DEBUG: Appending existing text file: {each_file}")
            response.append(
                DecomposedFileInfo(name=os.path.basename(each_file), file_path=each_file)
            )

        print(f"DEBUG: Decompose completed successfully. Returning {len(response)} items.")
        return response
        
    except HTTPException as he:
        print(f"DEBUG: HTTPException caught in decompose: {he.detail}")
        raise he
    except Exception as e:
        print("ERROR: Exception in decompose_files:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error during decomposition: {str(e)}")


@FILES_ROUTER.post("/update")
async def update_files(
    file_path: Annotated[str, Body()],
    file: Annotated[UploadFile, File()],
):
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"message": "File updated successfully"}
