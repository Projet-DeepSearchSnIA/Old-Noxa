from django.core.exceptions import ValidationError

def pdfUploadPath(instance, filename):
    return f"pdf/{filename}"

def validatePdf(file):
    if not file.name.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are allowed...")