import enum


class UserRole(str, enum.Enum):
    """SRS §5: Rol Bazlı Erişim (RBAC)."""

    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    AUDITOR = "AUDITOR"


class ExamStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


class PaperStatus(str, enum.Enum):
    """Bir sınav kağıdının yaşam döngüsü.

    PENDING   -> yüklendi, kuyrukta AI'ı bekliyor
    AI_SCORED -> AI okudu ve puanladı; akademisyen onayı bekliyor
    APPROVED  -> akademisyen onayladı; not kesinleşti (SRS §3.2 Human-in-the-Loop)
    FAILED    -> okuma/puanlama başarısız (bozuk görsel, model hatası vb.)
    """

    PENDING = "PENDING"
    AI_SCORED = "AI_SCORED"
    APPROVED = "APPROVED"
    FAILED = "FAILED"
