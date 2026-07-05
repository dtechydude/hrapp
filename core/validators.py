"""
core/validators.py

Shared, reusable validators for any FileField/ImageField in the
project. Keeping these here (instead of redefining a max-size check
in every app that accepts an upload) means the same security rule
applies everywhere: Company logos, staff passports/signatures,
certificates, payslips, etc.
"""
from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE_MB = 2
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "jpg", "jpeg", "png"]


def validate_file_size(file, max_mb: int = MAX_UPLOAD_SIZE_MB) -> None:
    """
    Rejects uploads above `max_mb` megabytes. Cheap, dependency-free
    guard against someone using a form upload field to fill shared
    hosting disk quota (relevant on PythonAnywhere Free / cPanel).
    """
    limit_bytes = max_mb * 1024 * 1024
    if file.size > limit_bytes:
        raise ValidationError(f"File too large. Maximum allowed size is {max_mb}MB.")