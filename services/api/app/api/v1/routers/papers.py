"""SRS GÖREV 3 — Presigned URL ile güvenli dosya yükleme.

Akış (mobil uygulamanın izlediği yol):

  1. POST /exams/{id}/papers/upload-url  -> API kağıt kaydını PENDING açar,
                                            imzalı bir PUT URL'i döner
  2. PUT <upload_url>                    -> istemci dosyayı DOĞRUDAN MinIO'ya yükler
                                            (API'den geçmez)
  3. POST /papers/{id}/confirm           -> yükleme bitti; kağıt işleme kuyruğuna girer
                                            (GÖREV 4)

Kaydı 1. adımda açıyoruz çünkü aksi halde MinIO'ya yüklenmiş ama veritabanında
karşılığı olmayan "yetim" dosyalar birikir.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sinavokuma_shared import Exam, ExamStatus, PaperStatus, StudentPaper, UserRole
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, get_readable_exam, require_role
from app.schemas.paper import PaperRead, UploadUrlRequest, UploadUrlResponse
from app.services import queue, storage

router = APIRouter(tags=["papers"])

WriteAccess = Annotated[object, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))]


@router.post(
    "/exams/{exam_id}/papers/upload-url",
    response_model=UploadUrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Kağıt kaydı aç ve imzalı yükleme URL'i al",
)
async def create_upload_url(
    payload: UploadUrlRequest,
    exam: Annotated[Exam, Depends(get_readable_exam)],
    db: DbSession,
    _: WriteAccess,
):
    try:
        object_key = storage.build_object_key(exam.id, payload.student_no, payload.extension)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    paper = StudentPaper(
        exam_id=exam.id,
        student_no=payload.student_no,
        image_url=object_key,
        status=PaperStatus.PENDING,
    )
    db.add(paper)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bu sınavda {payload.student_no} numaralı öğrencinin kağıdı zaten var.",
        ) from exc
    await db.refresh(paper)

    return UploadUrlResponse(
        paper_id=paper.id,
        object_key=object_key,
        upload_url=storage.presigned_put_url(object_key),
        expires_in_seconds=settings.presigned_url_ttl_seconds,
    )


@router.post(
    "/papers/{paper_id}/confirm",
    response_model=PaperRead,
    summary="Yükleme tamamlandı — kağıdı AI işleme kuyruğuna gönder (GÖREV 4)",
)
async def confirm_upload(paper_id: int, user: CurrentUser, db: DbSession, _: WriteAccess):
    paper = await db.get(StudentPaper, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kağıt bulunamadı.")

    # Kağıdın üstündeki sınav/ders bu kullanıcının mı? (satır bazlı erişim)
    await get_readable_exam(paper.exam_id, user, db)

    # Dosya gerçekten MinIO'da mı? İstemci upload-url alıp PUT'u atlamış olabilir;
    # doğrulamazsak worker olmayan bir dosyayı indirmeye çalışıp hata döngüsüne girer.
    if not storage.object_exists(paper.image_url):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dosya depoda bulunamadı. Önce presigned URL'e yükleme yapın.",
        )

    # Aynı kağıt iki kez onaylanırsa iki kez işlenir ve GPU boşa yanar.
    if paper.status != PaperStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Kağıt zaten işlenmiş (durum: {paper.status.value}).",
        )

    exam = await db.get(Exam, paper.exam_id)
    if exam is not None and exam.status == ExamStatus.DRAFT:
        exam.status = ExamStatus.PROCESSING

    await db.commit()
    await queue.publish_paper_for_processing(paper.id, paper.exam_id, paper.image_url)
    await db.refresh(paper)
    return paper


@router.get("/exams/{exam_id}/papers", response_model=list[PaperRead])
async def list_papers(exam: Annotated[Exam, Depends(get_readable_exam)], db: DbSession):
    result = await db.execute(
        select(StudentPaper)
        .where(StudentPaper.exam_id == exam.id)
        .order_by(StudentPaper.student_no)
    )
    return list(result.scalars().all())
