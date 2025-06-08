from pathlib import Path

import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(title="Static File Server", version="1.0.0")

# Static folder configuration
STATIC_DIR = Path("files")
STATIC_DIR.mkdir(exist_ok=True)


@app.get("/{path:path}")
async def get_file(path: str):
    """
    Get a file from the static directory.
    Supports both text and binary files.
    """
    if not path:
        # List directory contents
        files = []
        for item in STATIC_DIR.iterdir():
            if item.is_file():
                files.append(
                    {"name": item.name, "size": item.stat().st_size, "type": "file"}
                )
            elif item.is_dir():
                files.append({"name": item.name, "type": "directory"})
        return {"files": files}

    file_path = STATIC_DIR / path

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Check if it's a directory
    if file_path.is_dir():
        files = []
        for item in file_path.iterdir():
            if item.is_file():
                files.append(
                    {"name": item.name, "size": item.stat().st_size, "type": "file"}
                )
            elif item.is_dir():
                files.append({"name": item.name, "type": "directory"})
        return {"path": path, "files": files}

    # Return the file
    return FileResponse(
        path=file_path, filename=file_path.name, media_type="application/octet-stream"
    )


@app.post("/{path:path}")
async def upload_file(path: str, file: UploadFile = File(...)):
    """
    Upload a file to the static directory.
    Creates necessary subdirectories if they don't exist.
    """
    # Construct the full file path
    file_path = STATIC_DIR / path

    # Create parent directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file already exists
    if file_path.exists():
        raise HTTPException(status_code=409, detail="File already exists")

    # Write the file
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return {
        "message": "File uploaded successfully",
        "path": path,
        "filename": file.filename,
        "size": len(content),
    }


@app.delete("/{path:path}")
async def delete_file(path: str):
    """
    Delete a file or directory from the static directory.
    """
    if not path:
        raise HTTPException(status_code=400, detail="Path cannot be empty")

    file_path = STATIC_DIR / path

    # Check if file/directory exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File or directory not found")

    if file_path.is_file():
        file_path.unlink()
        return {"message": "File deleted successfully", "path": path}
    elif file_path.is_dir():
        # Remove directory (only if empty)
        try:
            file_path.rmdir()
            return {"message": "Directory deleted successfully", "path": path}
        except OSError:
            raise HTTPException(status_code=400, detail="Directory is not empty")
