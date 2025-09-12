"""Data ingestion pipeline for ISU archive data."""

import asyncio
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import aiofiles
import requests
from sqlalchemy.orm import Session
from src.models import Skater, Competition, Result, Video
from src.config import settings

logger = logging.getLogger(__name__)


class ISUDataIngestion:
    """Handles ingestion of ISU archive data."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.base_url = "https://isu.org/api"  # Example ISU API endpoint
    
    async def ingest_skater_bios(self, data_file: str) -> List[Skater]:
        """Ingest skater biographical data."""
        skaters = []
        
        try:
            async with aiofiles.open(data_file, 'r') as file:
                content = await file.read()
                skater_data = json.loads(content)
                
                for skater_info in skater_data:
                    skater = Skater(
                        name=skater_info.get('name'),
                        country=skater_info.get('country'),
                        birth_date=self._parse_date(skater_info.get('birth_date')),
                        discipline=skater_info.get('discipline'),
                        bio=skater_info.get('bio'),
                        achievements=skater_info.get('achievements', {})
                    )
                    
                    # Check if skater already exists
                    existing = self.db_session.query(Skater).filter(
                        Skater.name == skater.name,
                        Skater.country == skater.country
                    ).first()
                    
                    if not existing:
                        self.db_session.add(skater)
                        skaters.append(skater)
                        logger.info(f"Added skater: {skater.name} from {skater.country}")
                    else:
                        # Update existing skater
                        existing.bio = skater.bio
                        existing.achievements = skater.achievements
                        existing.updated_at = datetime.utcnow()
                        skaters.append(existing)
                        logger.info(f"Updated skater: {existing.name}")
                
                self.db_session.commit()
                
        except Exception as e:
            logger.error(f"Error ingesting skater bios: {e}")
            self.db_session.rollback()
            
        return skaters
    
    async def ingest_competition_results(self, data_file: str) -> List[Result]:
        """Ingest competition results data."""
        results = []
        
        try:
            async with aiofiles.open(data_file, 'r') as file:
                content = await file.read()
                result_data = json.loads(content)
                
                for result_info in result_data:
                    # First ensure competition exists
                    competition = await self._get_or_create_competition(result_info.get('competition'))
                    
                    # Get or create skater
                    skater = await self._get_or_create_skater(result_info.get('skater'))
                    
                    result = Result(
                        skater_id=skater.id,
                        competition_id=competition.id,
                        position=result_info.get('position'),
                        total_score=result_info.get('total_score'),
                        short_program_score=result_info.get('short_program_score'),
                        free_program_score=result_info.get('free_program_score'),
                        technical_score=result_info.get('technical_score'),
                        component_score=result_info.get('component_score'),
                        deductions=result_info.get('deductions', 0.0),
                        video_url=result_info.get('video_url')
                    )
                    
                    self.db_session.add(result)
                    results.append(result)
                    
                self.db_session.commit()
                logger.info(f"Ingested {len(results)} competition results")
                
        except Exception as e:
            logger.error(f"Error ingesting competition results: {e}")
            self.db_session.rollback()
            
        return results
    
    async def ingest_video_metadata(self, data_file: str) -> List[Video]:
        """Ingest video metadata and transcripts."""
        videos = []
        
        try:
            async with aiofiles.open(data_file, 'r') as file:
                content = await file.read()
                video_data = json.loads(content)
                
                for video_info in video_data:
                    video = Video(
                        title=video_info.get('title'),
                        url=video_info.get('url'),
                        thumbnail_url=video_info.get('thumbnail_url'),
                        duration=video_info.get('duration'),
                        skater_id=video_info.get('skater_id'),
                        competition_id=video_info.get('competition_id'),
                        program_type=video_info.get('program_type'),
                        transcript=video_info.get('transcript'),
                        metadata=video_info.get('metadata', {})
                    )
                    
                    # Check if video already exists
                    existing = self.db_session.query(Video).filter(
                        Video.url == video.url
                    ).first()
                    
                    if not existing:
                        self.db_session.add(video)
                        videos.append(video)
                        logger.info(f"Added video: {video.title}")
                    
                self.db_session.commit()
                
        except Exception as e:
            logger.error(f"Error ingesting video metadata: {e}")
            self.db_session.rollback()
            
        return videos
    
    async def fetch_live_data(self) -> Dict[str, Any]:
        """Fetch live data from ISU APIs."""
        try:
            # Example of fetching live competition data
            response = requests.get(f"{self.base_url}/competitions/current")
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch live data: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            return {}
    
    async def _get_or_create_competition(self, comp_data: Dict[str, Any]) -> Competition:
        """Get existing competition or create new one."""
        existing = self.db_session.query(Competition).filter(
            Competition.name == comp_data.get('name'),
            Competition.year == comp_data.get('year')
        ).first()
        
        if existing:
            return existing
        
        competition = Competition(
            name=comp_data.get('name'),
            year=comp_data.get('year'),
            location=comp_data.get('location'),
            start_date=self._parse_date(comp_data.get('start_date')),
            end_date=self._parse_date(comp_data.get('end_date')),
            discipline=comp_data.get('discipline'),
            level=comp_data.get('level')
        )
        
        self.db_session.add(competition)
        self.db_session.flush()  # Get the ID
        return competition
    
    async def _get_or_create_skater(self, skater_data: Dict[str, Any]) -> Skater:
        """Get existing skater or create new one."""
        existing = self.db_session.query(Skater).filter(
            Skater.name == skater_data.get('name'),
            Skater.country == skater_data.get('country')
        ).first()
        
        if existing:
            return existing
        
        skater = Skater(
            name=skater_data.get('name'),
            country=skater_data.get('country'),
            birth_date=self._parse_date(skater_data.get('birth_date')),
            discipline=skater_data.get('discipline'),
            bio=skater_data.get('bio', ''),
            achievements=skater_data.get('achievements', {})
        )
        
        self.db_session.add(skater)
        self.db_session.flush()  # Get the ID
        return skater
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y'):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None


class DataValidator:
    """Validates ingested data quality."""
    
    @staticmethod
    def validate_skater_data(skater_data: Dict[str, Any]) -> bool:
        """Validate skater data completeness."""
        required_fields = ['name', 'country']
        return all(field in skater_data and skater_data[field] for field in required_fields)
    
    @staticmethod
    def validate_result_data(result_data: Dict[str, Any]) -> bool:
        """Validate competition result data."""
        required_fields = ['skater', 'competition']
        return all(field in result_data for field in required_fields)
    
    @staticmethod
    def validate_video_data(video_data: Dict[str, Any]) -> bool:
        """Validate video metadata."""
        required_fields = ['title', 'url']
        return all(field in video_data and video_data[field] for field in required_fields)