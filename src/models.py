# StoryRequest Pydantic model (used in tests)
import pymysql
pymysql.install_as_MySQLdb()
from pydantic import BaseModel
from typing import Optional, Dict, List
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel
from typing import Optional, Dict, List
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Date, JSON, ForeignKey
Base = declarative_base()


# StoryResponse Pydantic model
class StoryResponse(BaseModel):
	id: int
	title: str
	content: str
	skater_ids: Optional[List[int]] = None
	audience: Optional[str] = None

	class Config:
		from_attributes = True

# VideoResponse Pydantic model
class VideoResponse(BaseModel):
	id: int
	title: str
	url: str
	duration: int
	program_type: str
	transcript: str

	class Config:
		from_attributes = True
# --- Pydantic response models ---
class VideoResponse(BaseModel):
	id: int
	title: str
	url: str
	duration: int
	program_type: str
	transcript: str

	class Config:
		from_attributes = True

class StoryRequest(BaseModel):
	skater_ids: Optional[List[int]] = None
	story_type: str = "profile"
	audience: str = "general"
	length: str = "medium"

	class Config:
		from_attributes = True

class ResultResponse(BaseModel):
	id: int
	skater_id: int
	competition_id: int
	position: int
	score: str

	class Config:
		from_attributes = True

class SkaterResponse(BaseModel):
	id: int
	name: str
	country: str
	birth_date: Optional[str] = None
	discipline: Optional[str] = None
	bio: Optional[str] = None
	achievements: Optional[Dict] = None

	class Config:
		from_attributes = True

class CompetitionResponse(BaseModel):
	id: int
	name: str
	year: Optional[int] = None
	location: Optional[str] = None
	start_date: Optional[str] = None
	end_date: Optional[str] = None
	discipline: Optional[str] = None
	level: Optional[str] = None

	class Config:
		from_attributes = True

# --- SQLAlchemy models ---
class Skater(Base):
	__tablename__ = 'skaters'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	country = Column(String, nullable=False)
	birth_date = Column(Date)
	discipline = Column(String)
	bio = Column(String)
	achievements = Column(JSON)
	# Add relationships if needed

class Competition(Base):
	__tablename__ = 'competitions'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	year = Column(Integer)
	location = Column(String)
	start_date = Column(Date)
	end_date = Column(Date)
	discipline = Column(String)
	level = Column(String)

class Result(Base):
	__tablename__ = 'results'
	id = Column(Integer, primary_key=True)
	skater_id = Column(Integer, ForeignKey('skaters.id'))
	competition_id = Column(Integer, ForeignKey('competitions.id'))
	position = Column(Integer)
	score = Column(String)
	# Relationships
	skater = relationship('Skater')
	competition = relationship('Competition')

class Video(Base):
	__tablename__ = 'videos'
	id = Column(Integer, primary_key=True)
	title = Column(String, nullable=False)
	url = Column(String, nullable=False)
	duration = Column(Integer)
	program_type = Column(String)
	transcript = Column(String)