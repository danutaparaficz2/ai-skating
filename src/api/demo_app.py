"""Simplified FastAPI application for demo without heavy dependencies."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    logger.warning("Static directory not found, skipping static file mounting")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    try:
        with open("templates/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>Data on Ice</title></head>
            <body>
                <h1>🛸 Data on Ice - ISU Archive API</h1>
                <p>API is running! Visit <a href="/docs">/docs</a> for interactive documentation.</p>
                <h2>Demo Endpoints:</h2>
                <ul>
                    <li><a href="/api/info">/api/info</a> - API information</li>
                    <li><a href="/demo/skaters">/demo/skaters</a> - Sample skaters</li>
                    <li><a href="/demo/search?q=Nathan">/demo/search?q=Nathan</a> - Demo search</li>
                    <li><a href="/health">/health</a> - Health check</li>
                </ul>
            </body>
        </html>
        """)


@app.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "ISU skating data transformation API powered by Alibaba Cloud AI",
        "technologies": [
            "Qwen LLM for story generation",
            "AnalyticDB for data storage", 
            "OpenSearch for content discovery",
            "PAI-EAS for ML model deployment",
            "ECS-GPU for high-performance computing"
        ],
        "features": [
            "AI-powered story generation",
            "Advanced search capabilities",
            "Predictive analytics",
            "Multi-audience content",
            "Real-time data processing"
        ],
        "endpoints": {
            "skaters": "/demo/skaters/",
            "search": "/demo/search/",
            "stories": "/demo/stories/",
            "health": "/health"
        }
    }


@app.get("/demo/skaters")
async def get_demo_skaters():
    """Get demo skater data."""
    skaters = [
        {
            "id": 1,
            "name": "Nathan Chen",
            "country": "USA",
            "discipline": "singles",
            "bio": "American figure skater known for his quadruple jumps and consistency.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 3,
                "grand_prix_finals": 1
            }
        },
        {
            "id": 2,
            "name": "Yuzuru Hanyu",
            "country": "JPN", 
            "discipline": "singles",
            "bio": "Two-time Olympic champion known for his artistic expression and technical mastery.",
            "achievements": {
                "olympic_gold": 2,
                "world_championships": 2,
                "grand_prix_finals": 4
            }
        },
        {
            "id": 3,
            "name": "Sui Wenjing",
            "country": "CHN",
            "discipline": "pairs",
            "bio": "Chinese pairs skater, Olympic champion with partner Han Cong.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 2,
                "grand_prix_finals": 2
            }
        }
    ]
    return {"skaters": skaters, "total": len(skaters)}


@app.get("/demo/search")
async def demo_search(
    q: str = Query(..., min_length=1, description="Search query"),
    content_type: Optional[str] = Query(None, description="Content type filter"),
    limit: int = Query(10, ge=1, le=50, description="Number of results")
):
    """Demo search functionality."""
    
    # Simulate search results based on query
    all_results = [
        {
            "id": "skater_1",
            "type": "skater",
            "title": "Nathan Chen",
            "content": "American figure skater known for his quadruple jumps and Olympic gold medal.",
            "country": "USA",
            "discipline": "singles",
            "score": 0.95
        },
        {
            "id": "skater_2", 
            "type": "skater",
            "title": "Yuzuru Hanyu",
            "content": "Japanese two-time Olympic champion with exceptional artistry.",
            "country": "JPN",
            "discipline": "singles", 
            "score": 0.90
        },
        {
            "id": "competition_1",
            "type": "competition",
            "title": "Winter Olympics 2022",
            "content": "Beijing Olympics figure skating competitions with record performances.",
            "year": 2022,
            "location": "Beijing",
            "score": 0.85
        },
        {
            "id": "video_1",
            "type": "video",
            "title": "Nathan Chen Olympic Free Skate",
            "content": "Historic Olympic free skate performance with five quadruple jumps.",
            "duration": 285,
            "program_type": "free_program",
            "score": 0.80
        }
    ]
    
    # Filter by query (simple contains match)
    query_lower = q.lower()
    filtered_results = [
        result for result in all_results 
        if query_lower in result["title"].lower() or query_lower in result["content"].lower()
    ]
    
    # Filter by content type if specified
    if content_type:
        filtered_results = [r for r in filtered_results if r["type"] == content_type]
    
    # Sort by score and limit
    filtered_results.sort(key=lambda x: x["score"], reverse=True)
    limited_results = filtered_results[:limit]
    
    return {
        "query": q,
        "total": len(filtered_results),
        "results": limited_results,
        "demo_note": "This is demo search data. Production would use Alibaba OpenSearch with real ISU archive data."
    }


@app.get("/demo/stories/generate")
async def demo_generate_story(
    story_type: str = Query("profile", description="Type of story to generate"),
    skater_name: Optional[str] = Query("Nathan Chen", description="Skater name for story"),
    audience: str = Query("general", description="Target audience")
):
    """Demo story generation using AI."""
    
    # Simulate AI-generated stories
    stories = {
        "profile": {
            "title": f"The Remarkable Journey of {skater_name}",
            "content": f"""In the world of figure skating, few athletes capture the imagination quite like {skater_name}. 
            With a combination of technical precision and artistic flair, they have redefined what it means to compete 
            at the highest level. From early morning training sessions to standing atop Olympic podiums, their journey 
            represents the very best of human determination and skill.
            
            Through years of dedication and countless hours of practice, {skater_name} has emerged as one of the sport's 
            most compelling figures. Their performances transcend mere competition, offering audiences moments of pure 
            artistry and athletic excellence that will be remembered for generations to come.""",
            "summary": f"An inspiring profile of {skater_name}'s journey from promising young skater to world champion.",
            "tags": ["profile", "inspiration", "skating", skater_name.lower().replace(" ", "-")]
        },
        "competition_recap": {
            "title": "Thrilling Competition Delivers Unforgettable Moments",
            "content": f"""The arena was electric as skaters from around the world took to the ice for one of the season's 
            most anticipated competitions. Record-breaking scores, stunning comebacks, and emotional performances created 
            a night that fans will remember for years to come.
            
            {skater_name} delivered a masterful performance that showcased the very best of figure skating. The level 
            of competition has never been higher, with each performance pushing the boundaries of what's possible on ice. 
            Technical innovation combined with artistic expression created a truly spectacular evening of sport.""",
            "summary": "A thrilling competition recap featuring outstanding performances and memorable moments.",
            "tags": ["competition", "recap", "skating", "highlights"]
        },
        "prediction": {
            "title": f"Analyzing {skater_name}: What to Expect Next",
            "content": f"""Based on recent performance trends and historical data, several factors point to an exciting 
            upcoming competition season for {skater_name}. Current form suggests we may see new personal bests, while 
            their technical evolution continues to drive the sport forward.
            
            The data reveals interesting patterns in scoring and consistency that indicate strong potential for upcoming 
            events. Technical elements have shown steady improvement, while program components remain at elite levels. 
            This combination suggests fans can expect exceptional performances in the coming season.""",
            "summary": f"Data-driven analysis predicting {skater_name}'s performance in upcoming competitions.",
            "tags": ["prediction", "analysis", "data", skater_name.lower().replace(" ", "-")]
        }
    }
    
    story = stories.get(story_type, stories["profile"])
    
    return {
        "story": story,
        "generation_info": {
            "ai_model": "Qwen LLM (Demo Mode)",
            "audience": audience,
            "generated_at": datetime.utcnow().isoformat(),
            "demo_note": "This is a demo story. Production would use Alibaba Qwen LLM for real AI generation."
        }
    }


@app.get("/demo/trending")
async def get_demo_trending():
    """Get demo trending content."""
    trending = [
        {
            "id": "trend_1",
            "type": "video",
            "title": "🔥 World Championships Highlights",
            "description": "The most spectacular moments from this year's World Championships",
            "views": 2100000,
            "engagement_score": 95,
            "trending_rank": 1
        },
        {
            "id": "trend_2", 
            "type": "analysis",
            "title": "📈 Olympic Predictions Analysis",
            "description": "Data-driven insights into Olympic medal predictions",
            "views": 850000,
            "engagement_score": 88,
            "trending_rank": 2
        },
        {
            "id": "trend_3",
            "type": "story",
            "title": "⭐ Rising Junior Talents",
            "description": "Meet the next generation of skating stars",
            "views": 620000,
            "engagement_score": 82,
            "trending_rank": 3
        }
    ]
    
    return {
        "trending": trending,
        "period": "Last 7 days",
        "demo_note": "This is demo trending data based on simulated engagement metrics."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "service": "Data on Ice API",
        "dependencies": {
            "qwen_llm": "demo_mode",
            "opensearch": "demo_mode", 
            "analyticdb": "demo_mode"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)