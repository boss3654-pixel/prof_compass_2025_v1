# hh_bot/db/models/documents.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..base import Base
from ...enums import DocumentTypeEnum # Относительный импорт

class GeneratedDocument(Base):
    """Модель для хранения сгенерированных документов (резюме, писем)."""

    __tablename__ = "generated_documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(
        Integer, ForeignKey("vacancies.id"), nullable=True
    )  # Может быть None
    doc_type = Column(
        SAEnum(
            DocumentTypeEnum,
            name="document_type_enum",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False
    )
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="generated_documents")

    def __repr__(self):
        return f"<GeneratedDocument(id={self.id}, user_id={self.user_id}, doc_type='{self.doc_type}')>"