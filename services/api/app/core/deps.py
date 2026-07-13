"""SRS §5: Rol Bazlı Erişim Kontrolü (RBAC).

Yetkilendirme burada, tek yerde zorlanır. Endpoint'lerin içinde rol kontrolü
tekrar edilmez — unutulan bir kontrol güvenlik açığıdır.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Course, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Kimlik doğrulanamadı.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise CREDENTIALS_ERROR
    except jwt.PyJWTError as exc:
        raise CREDENTIALS_ERROR from exc

    user = await db.get(User, int(user_id))
    if user is None:
        raise CREDENTIALS_ERROR
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hesap devre dışı.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


def require_role(*allowed: UserRole):
    """Endpoint'i belirli rollere kısıtlar.

    Kullanım:
        @router.post("/exams", dependencies=[Depends(require_role(UserRole.TEACHER))])
    """

    async def checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Bu işlem için yetkiniz yok. Gerekli rol: "
                    f"{', '.join(r.value for r in allowed)}"
                ),
            )
        return user

    return checker


async def get_owned_course(course_id: int, user: CurrentUser, db: DbSession) -> Course:
    """Dersi getirir, ama satır bazlı erişimi de zorlar.

    Bir TEACHER yalnızca kendi derslerine dokunabilir. ADMIN ve AUDITOR hepsini
    görebilir (AUDITOR salt-okunur; yazma yetkisi ayrıca `require_role` ile kesilir).

    "Ders yok" ve "ders var ama senin değil" durumlarının ikisine de 404 dönüyoruz —
    403 dönmek, saldırgana o ID'de bir dersin var olduğunu sızdırırdı.
    """
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ders bulunamadı.")

    if user.role == UserRole.TEACHER and course.teacher_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ders bulunamadı.")

    return course


async def get_readable_exam(exam_id: int, user: CurrentUser, db: DbSession):
    """Sınavı getirir ve üstündeki dersin sahipliğini doğrular."""
    from app.models import Exam

    exam = await db.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sınav bulunamadı.")

    await get_owned_course(exam.course_id, user, db)
    return exam
