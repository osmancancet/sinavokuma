from pydantic import BaseModel, ConfigDict, Field
from sinavokuma_shared import PaperStatus


class UploadUrlRequest(BaseModel):
    student_no: str = Field(min_length=1, max_length=32, examples=["20210101"])
    extension: str = Field(default="jpg", examples=["jpg", "png"])


class UploadUrlResponse(BaseModel):
    """Mobil uygulama `upload_url`'e dosyayı PUT eder, sonra /confirm'e `paper_id` ile döner."""

    paper_id: int
    object_key: str
    upload_url: str
    expires_in_seconds: int


class PaperRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    student_no: str
    image_url: str
    status: PaperStatus
    error_message: str | None
