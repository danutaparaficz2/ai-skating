"""FastAPI application for the Data on Ice project."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from src.config import settings, get_database_url
from src.models import (
    Base, Skater, Competition, Result, Video,
    SkaterResponse, CompetitionResponse, ResultResponse, VideoResponse,
    StoryRequest, StoryResponse
)
from src.ai_processing import StoryGenerator
from src.search import SearchService
from src.data_ingestion import ISUDataIngestion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(get_database_url()) if settings.analyticdb_user else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

# Initialize FastAPI app
app = FastAPI(
    title="Data on Ice - ISU Archive API",
    description="Transform ISU skating data into engaging narratives",
    version=settings.app_version
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
story_generator = StoryGenerator()
search_service = SearchService()


# Dependency to get database session
def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "ISU skating data transformation API",
        "endpoints": {
            "skaters": "/skaters/",
            "competitions": "/competitions/",
            "results": "/results/",
            "videos": "/videos/",
            "stories": "/stories/",
            "search": "/search/",
            "docs": "/docs"
        }
    }


# Skater endpoints
@app.get("/skaters/", response_model=List[SkaterResponse])
async def get_skaters(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None),
    discipline: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of skaters with optional filtering."""
    query = db.query(Skater)
    
    if country:
        query = query.filter(Skater.country == country)
    if discipline:
        query = query.filter(Skater.discipline == discipline)
    
    skaters = query.offset(skip).limit(limit).all()
    return skaters


@app.get("/skaters/{skater_id}", response_model=SkaterResponse)
async def get_skater(skater_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Get specific skater by ID."""
    skater = db.query(Skater).filter(Skater.id == skater_id).first()
    if not skater:
        raise HTTPException(status_code=404, detail="Skater not found")
    return skater


@app.get("/skaters/{skater_id}/results", response_model=List[ResultResponse])
async def get_skater_results(
    skater_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Get competition results for a specific skater."""
    results = db.query(Result).filter(Result.skater_id == skater_id).all()
    return results


@app.get("/skaters/{skater_id}/videos", response_model=List[VideoResponse])
async def get_skater_videos(
    skater_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Get videos for a specific skater."""
    videos = db.query(Video).filter(Video.skater_id == skater_id).all()
    return videos


# Competition endpoints
@app.get("/competitions/", response_model=List[CompetitionResponse])
async def get_competitions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    year: Optional[int] = Query(None),
    discipline: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of competitions with optional filtering."""
    query = db.query(Competition)
    
    if year:
        query = query.filter(Competition.year == year)
    if discipline:
        query = query.filter(Competition.discipline == discipline)
    
    competitions = query.offset(skip).limit(limit).all()
    return competitions


@app.get("/competitions/{competition_id}", response_model=CompetitionResponse)
async def get_competition(
    competition_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Get specific competition by ID."""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    return competition


@app.get("/competitions/{competition_id}/results", response_model=List[ResultResponse])
async def get_competition_results(
    competition_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Get results for a specific competition."""
    results = db.query(Result).filter(Result.competition_id == competition_id).order_by(Result.position).all()
    return results


# Video endpoints
@app.get("/videos/", response_model=List[VideoResponse])
async def get_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    skater_id: Optional[int] = Query(None),
    competition_id: Optional[int] = Query(None),
    program_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of videos with optional filtering."""
    query = db.query(Video)
    
    if skater_id:
        query = query.filter(Video.skater_id == skater_id)
    if competition_id:
        query = query.filter(Video.competition_id == competition_id)
    if program_type:
        query = query.filter(Video.program_type == program_type)
    
    videos = query.offset(skip).limit(limit).all()
    return videos


@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Get specific video by ID."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


# Story generation endpoints
@app.post("/stories/generate", response_model=StoryResponse)
async def generate_story(request: StoryRequest, db: Session = Depends(get_db)):
    """Generate personalized stories based on request parameters."""
    try:
        if request.story_type == "profile" and request.skater_ids:
            # Generate skater profile story
            skater_id = request.skater_ids[0]
            skater = db.query(Skater).filter(Skater.id == skater_id).first()
            if not skater:
                raise HTTPException(status_code=404, detail="Skater not found")
            
            # Get related data
            results = db.query(Result).filter(Result.skater_id == skater_id).limit(10).all()
            videos = db.query(Video).filter(Video.skater_id == skater_id).limit(5).all()
            
            story = await story_generator.generate_skater_profile(
                skater, results, videos, request.audience
            )
            return story
            
        elif request.story_type == "competition_recap" and request.competition_ids:
            # Generate competition recap
            competition_id = request.competition_ids[0]
            competition = db.query(Competition).filter(Competition.id == competition_id).first()
            if not competition:
                raise HTTPException(status_code=404, detail="Competition not found")
            
            results = db.query(Result).filter(Result.competition_id == competition_id).all()
            videos = db.query(Video).filter(Video.competition_id == competition_id).limit(5).all()
            
            story = await story_generator.generate_competition_recap(
                competition, results, videos, request.audience
            )
            return story
            
        elif request.story_type == "prediction" and request.skater_ids:
            # Generate prediction story
            skater_id = request.skater_ids[0]
            skater = db.query(Skater).filter(Skater.id == skater_id).first()
            if not skater:
                raise HTTPException(status_code=404, detail="Skater not found")
            
            # Get historical results for prediction
            results = db.query(Result).filter(Result.skater_id == skater_id).order_by(Result.created_at.desc()).limit(10).all()
            
            story = await story_generator.generate_prediction(
                skater, results, "Upcoming World Championships", request.audience
            )
            return story
        
        else:
            raise HTTPException(status_code=400, detail="Invalid story request parameters")
            
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        raise HTTPException(status_code=500, detail="Story generation failed")


# Search endpoints
@app.get("/search/")
async def search_content(
    q: str = Query(..., min_length=1),
    content_types: Optional[List[str]] = Query(None),
    country: Optional[str] = Query(None),
    discipline: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Search across all content types."""
    try:
        filters = {}
        if country:
            filters["country"] = country
        if discipline:
            filters["discipline"] = discipline
        if year:
            filters["year_range"] = {"from": year, "to": year}
        
        results = await search_service.unified_search(
            query=q,
            content_types=content_types,
            filters=filters,
            page=page,
            page_size=page_size
        )
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/search/skaters")
async def search_skaters(
    q: str = Query(..., min_length=1),
    country: Optional[str] = Query(None),
    discipline: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """Search specifically for skaters."""
    try:
        results = await search_service.client.search_skaters(
            query=q,
            country=country,
            discipline=discipline,
            size=limit
        )
        return {"query": q, "results": results}
    except Exception as e:
        logger.error(f"Skater search error: {e}")
        raise HTTPException(status_code=500, detail="Skater search failed")


@app.get("/search/competitions")
async def search_competitions(
    q: str = Query(..., min_length=1),
    year: Optional[int] = Query(None),
    discipline: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """Search specifically for competitions."""
    try:
        results = await search_service.client.search_competitions(
            query=q,
            year=year,
            discipline=discipline,
            size=limit
        )
        return {"query": q, "results": results}
    except Exception as e:
        logger.error(f"Competition search error: {e}")
        raise HTTPException(status_code=500, detail="Competition search failed")


# Recommendation endpoints
@app.get("/recommendations/{skater_id}")
async def get_recommendations(
    skater_id: int = Path(..., gt=0),
    limit: int = Query(5, ge=1, le=20)
):
    """Get content recommendations for a skater."""
    try:
        recommendations = await search_service.client.get_recommendations(skater_id, limit)
        return {"skater_id": skater_id, "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Recommendation failed")


@app.get("/trending/")
async def get_trending_content(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50)
):
    """Get trending content."""
    try:
        trending = await search_service.client.get_trending_content(days, limit)
        return {"period_days": days, "trending": trending}
    except Exception as e:
        logger.error(f"Trending content error: {e}")
        raise HTTPException(status_code=500, detail="Trending content failed")


# Data ingestion endpoints (for admin use)
@app.post("/admin/ingest/skaters")
async def ingest_skaters(file_path: str, db: Session = Depends(get_db)):
    """Ingest skater data from file."""
    try:
        ingestion = ISUDataIngestion(db)
        skaters = await ingestion.ingest_skater_bios(file_path)
        
        # Index in search
        for skater in skaters:
            await search_service.client.index_skater(skater)
        
        return {"message": f"Ingested {len(skaters)} skaters", "count": len(skaters)}
    except Exception as e:
        logger.error(f"Skater ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Skater ingestion failed")


@app.post("/admin/ingest/results")
async def ingest_results(file_path: str, db: Session = Depends(get_db)):
    """Ingest competition results from file."""
    try:
        ingestion = ISUDataIngestion(db)
        results = await ingestion.ingest_competition_results(file_path)
        
        # Index in search
        for result in results:
            await search_service.client.index_result(result)
        
        return {"message": f"Ingested {len(results)} results", "count": len(results)}
    except Exception as e:
        logger.error(f"Results ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Results ingestion failed")


@app.post("/admin/ingest/videos")
async def ingest_videos(file_path: str, db: Session = Depends(get_db)):
    """Ingest video metadata from file."""
    try:
        ingestion = ISUDataIngestion(db)
        videos = await ingestion.ingest_video_metadata(file_path)
        
        # Index in search
        for video in videos:
            await search_service.client.index_video(video)
        
        return {"message": f"Ingested {len(videos)} videos", "count": len(videos)}
    except Exception as e:
        logger.error(f"Video ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Video ingestion failed")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)