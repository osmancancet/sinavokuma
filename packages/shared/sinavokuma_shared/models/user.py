from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.models.base import Base, TimestampMixin
from sinavokuma_shared.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.TEACHER
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    courses: Mapped[list["Course"]] = relationship(  # noqa: F821
        back_populates="teacher", cascade="all, delete-orphan"
    )
