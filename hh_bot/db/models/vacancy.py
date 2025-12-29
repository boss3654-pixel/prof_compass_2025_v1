from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..base import Base
from ...enums import UserVacancyStatusEnum

class Vacancy(Base):
    __tablename__ = "vacancies"
    id = Column(Integer, primary_key=True, index=True)
    hh_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    company = Column(String)
    city = Column(String)
    salary = Column(String)
    link = Column(String)
    apply_url = Column(String, nullable=True)
    description_snippet = Column(Text)
    # ДЛЯ ОБСУЖДЕНИЯ: Можно рассмотреть `DateTime(timezone=True)` в будущем
    published_at = Column(DateTime)

    def __repr__(self):
        return f"<Vacancy(id={self.id}, hh_id='{self.hh_id}', title='{self.title}')>"

class UserVacancyStatus(Base):
    __tablename__ = "user_vacancy_status"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=False)
    
    status = Column(
        SAEnum(
            UserVacancyStatusEnum,
            name="uservacancystatusenum",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=UserVacancyStatusEnum.SENT,
        nullable=False,
    )
    # ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ: Колонка теперь "осведомлена" о часовых поясах
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="viewed_vacancies")
    vacancy = relationship("Vacancy")

    def __repr__(self):
        return f"<UserVacancyStatus(id={self.id}, user_id={self.user_id}, status='{self.status}')>"