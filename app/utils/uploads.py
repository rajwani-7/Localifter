import os
import secrets
from typing import Optional

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}


def _is_allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_obj: Optional[FileStorage], subfolder: str) -> Optional[str]:
    if not file_obj or not file_obj.filename:
        return None

    filename = secure_filename(file_obj.filename)
    if not _is_allowed(filename):
        raise ValueError("Unsupported file type")

    ext = filename.rsplit(".", 1)[1].lower()
    safe_name = f"{secrets.token_hex(12)}.{ext}"

    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, safe_name)
    file_obj.save(save_path)

    return os.path.join("uploads", subfolder, safe_name).replace("\\", "/")
