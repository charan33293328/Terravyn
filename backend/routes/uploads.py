from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil
import os
import uuid
import io
from pypdf import PdfReader, PdfWriter

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Secure directory for Aadhaar uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "secure_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB

@router.post("/identity-document")
async def upload_identity_document(
    file: UploadFile = File(...),
    password: str = Form(None)
):
    # 1. Validate Extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: PDF, JPG, JPEG, PNG.")
        
    # Read entire file into memory (since max size is 10MB)
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 10 MB limit.")

    # PDF encryption handling
    if ext == ".pdf":
        try:
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            if pdf_reader.is_encrypted:
                if not password:
                    # Specific error code so frontend knows it needs a password
                    raise HTTPException(status_code=423, detail="ENCRYPTED_PDF")
                
                # Attempt decryption
                if pdf_reader.decrypt(password) == 0:
                    raise HTTPException(status_code=400, detail="The password entered is incorrect. Please try again.")
                
                # Decrypt successful, generate an unencrypted PDF in memory
                pdf_writer = PdfWriter()
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                out_io = io.BytesIO()
                pdf_writer.write(out_io)
                file_bytes = out_io.getvalue()
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file.")

    # Generate unique filename to avoid collision
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Write the file (either decrypted PDF or original image/PDF)
    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e
        
    return {"status": "success", "document_path": unique_filename}

PRODUCT_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "public", "images", "products", "terravyn")
os.makedirs(PRODUCT_IMG_DIR, exist_ok=True)

@router.post("/product-image")
async def upload_product_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")
        
    unique_filename = f"prod_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(PRODUCT_IMG_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Return the URL path relative to frontend public
    return {"status": "success", "image_path": f"/images/products/terravyn/{unique_filename}"}
