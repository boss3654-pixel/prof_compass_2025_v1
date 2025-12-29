# hh_bot/db/models/user.py
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON, Boolean, Float, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..base import Base
from ...enums import EmploymentTypeEnum, ExperienceEnum

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    city = Column(String)
    desired_position = Column(String)
    skills = Column(Text)
    base_resume = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    search_filters = relationship(
        "SearchFilter",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    llm_settings = relationship(
        "LLMSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    viewed_vacancies = relationship(
        "UserVacancyStatus", back_populates="user", cascade="all, delete-orphan"
    )
    generated_documents = relationship("GeneratedDocument", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id='{self.telegram_id}', full_name='{self.full_name}')>"

class SearchFilter(Base):
    __tablename__ = "search_filters"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    position = Column(String)
    city = Column(String)
    salary_min = Column(Integer)
    remote = Column(Boolean, default=False)
    metro_stations = Column(JSON)
    freshness_days = Column(Integer, default=1)
    employment = Column(
        SAEnum(
            EmploymentTypeEnum,
            name="employment_type_enum",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True
    )
    experience = Column(
        SAEnum(
            ExperienceEnum,
            name="experience_enum",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True
    )
    employer_type = Column(String)

    user = relationship("User", back_populates="search_filters")

    def __repr__(self):
        return f"<SearchFilter(id={self.id}, user_id={self.user_id}, position='{self.position}')>"

class LLMSettings(Base):
    __tablename__ = "llm_settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=2048)

    user = relationship("User", back_populates="llm_settings")

    def __repr__(self):
        return f"<LLMSettings(id={self.id}, user_id={self.user_id}, base_url='{self.base_url}')>"