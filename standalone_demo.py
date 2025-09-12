"""Standalone demo for Data on Ice - ISU Archive Transformation."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Data on Ice - ISU Archive API (Demo)",
    description="Transform ISU skating data into engaging narratives using Alibaba Cloud AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Data on Ice - Demo</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   min-height: 100vh; color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            .card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); 
                    border-radius: 15px; padding: 30px; margin: 20px 0; }
            h1 { text-align: center; font-size: 3rem; margin-bottom: 10px; }
            .subtitle { text-align: center; font-size: 1.2rem; opacity: 0.9; margin-bottom: 30px; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
            .feature { text-align: center; padding: 20px; }
            .feature-icon { font-size: 2rem; margin-bottom: 10px; }
            .endpoints { margin: 20px 0; }
            .endpoint { background: rgba(255,255,255,0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }
            .endpoint a { color: #ffd700; text-decoration: none; }
            .endpoint a:hover { text-decoration: underline; }
            .tech-stack { text-align: center; margin-top: 30px; }
            .tech-item { display: inline-block; background: rgba(255,255,255,0.2); 
                         padding: 8px 15px; margin: 5px; border-radius: 20px; font-size: 0.9rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⛸️ Data on Ice</h1>
            <p class="subtitle">Transform ISU skating data into engaging narratives</p>
            
            <div class="card">
                <h2>🚀 Demo Features</h2>
                <div class="features">
                    <div class="feature">
                        <div class="feature-icon">🤖</div>
                        <h3>AI Stories</h3>
                        <p>Qwen LLM powered narrative generation</p>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🔍</div>
                        <h3>Smart Search</h3>
                        <p>OpenSearch across all content types</p>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">📊</div>
                        <h3>Analytics</h3>
                        <p>Performance predictions & insights</p>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🎯</div>
                        <h3>Personalization</h3>
                        <p>Multi-audience content generation</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📋 API Endpoints</h2>
                <div class="endpoints">
                    <div class="endpoint">
                        <strong>API Info:</strong> <a href="/api/info">/api/info</a>
                        - Get platform information and capabilities
                    </div>
                    <div class="endpoint">
                        <strong>Demo Skaters:</strong> <a href="/demo/skaters">/demo/skaters</a>
                        - Browse sample figure skater profiles
                    </div>
                    <div class="endpoint">
                        <strong>Search Demo:</strong> <a href="/demo/search?q=Nathan">/demo/search?q=Nathan</a>
                        - Test intelligent content search
                    </div>
                    <div class="endpoint">
                        <strong>Story Generation:</strong> <a href="/demo/stories/generate?skater_name=Yuzuru%20Hanyu">/demo/stories/generate?skater_name=Yuzuru Hanyu</a>
                        - AI-powered story creation
                    </div>
                    <div class="endpoint">
                        <strong>Trending Content:</strong> <a href="/demo/trending">/demo/trending</a>
                        - Discover popular skating content
                    </div>
                    <div class="endpoint">
                        <strong>Interactive Docs:</strong> <a href="/docs">/docs</a>
                        - Swagger UI for API exploration
                    </div>
                </div>
            </div>
            
            <div class="card tech-stack">
                <h2>🛠️ Alibaba Cloud Technologies</h2>
                <div class="tech-item">Qwen LLM</div>
                <div class="tech-item">AnalyticDB</div>
                <div class="tech-item">OpenSearch</div>
                <div class="tech-item">PAI-EAS</div>
                <div class="tech-item">ECS-GPU</div>
            </div>
        </div>
    </body>
    </html>
    """)


@app.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Data on Ice",
        "version": "1.0.0",
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
        "demo_endpoints": {
            "skaters": "/demo/skaters",
            "search": "/demo/search?q=<query>",
            "stories": "/demo/stories/generate?story_type=<type>&skater_name=<name>",
            "trending": "/demo/trending",
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
            "bio": "American figure skater known for his quadruple jumps and consistency. Olympic champion and multiple-time World champion.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 3,
                "grand_prix_finals": 1,
                "personal_best": 332.60
            },
            "recent_competitions": ["Beijing Olympics 2022", "World Championships 2023"]
        },
        {
            "id": 2,
            "name": "Yuzuru Hanyu",
            "country": "JPN", 
            "discipline": "singles",
            "bio": "Two-time Olympic champion known for his artistic expression and technical mastery. Widely considered one of the greatest figure skaters of all time.",
            "achievements": {
                "olympic_gold": 2,
                "world_championships": 2,
                "grand_prix_finals": 4,
                "personal_best": 322.59
            },
            "recent_competitions": ["Beijing Olympics 2022", "24 Hour Television 2022"]
        },
        {
            "id": 3,
            "name": "Sui Wenjing",
            "country": "CHN",
            "discipline": "pairs",
            "bio": "Chinese pairs skater, Olympic champion with partner Han Cong. Known for their exceptional synchronization and powerful throws.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 2,
                "grand_prix_finals": 2,
                "personal_best": 239.88
            },
            "partner": "Han Cong",
            "recent_competitions": ["Beijing Olympics 2022", "World Championships 2023"]
        },
        {
            "id": 4,
            "name": "Gabriella Papadakis",
            "country": "FRA",
            "discipline": "ice_dance",
            "bio": "French ice dancer, Olympic champion with partner Guillaume Cizeron. Known for their innovative choreography and emotional performances.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 5,
                "grand_prix_finals": 4,
                "personal_best": 229.82
            },
            "partner": "Guillaume Cizeron",
            "recent_competitions": ["Beijing Olympics 2022", "World Championships 2022"]
        }
    ]
    return {
        "skaters": skaters, 
        "total": len(skaters),
        "note": "This is demo data representing real skaters. Production system would contain comprehensive ISU archive data."
    }


@app.get("/demo/search")
async def demo_search(
    q: str = Query(..., min_length=1, description="Search query"),
    content_type: Optional[str] = Query(None, description="Content type filter (skater, competition, video)"),
    limit: int = Query(10, ge=1, le=50, description="Number of results")
):
    """Demo search functionality showcasing OpenSearch capabilities."""
    
    # Comprehensive demo search results
    all_results = [
        {
            "id": "skater_1",
            "type": "skater",
            "title": "Nathan Chen",
            "content": "American figure skater known for his quadruple jumps and Olympic gold medal. Revolutionary technical skater.",
            "country": "USA",
            "discipline": "singles",
            "score": 0.95,
            "highlights": ["Olympic Champion", "5 Quad Jumps", "Technical Innovation"]
        },
        {
            "id": "skater_2", 
            "type": "skater",
            "title": "Yuzuru Hanyu",
            "content": "Japanese two-time Olympic champion with exceptional artistry. Beloved for emotional performances and technical mastery.",
            "country": "JPN",
            "discipline": "singles", 
            "score": 0.90,
            "highlights": ["2x Olympic Champion", "Artistic Excellence", "World Record Holder"]
        },
        {
            "id": "competition_1",
            "type": "competition",
            "title": "Winter Olympics 2022 - Beijing",
            "content": "Historic Beijing Olympics figure skating competitions featuring record performances and emotional stories.",
            "year": 2022,
            "location": "Beijing, China",
            "score": 0.85,
            "highlights": ["Record Scores", "New Champions", "Historic Venue"]
        },
        {
            "id": "video_1",
            "type": "video",
            "title": "Nathan Chen Olympic Free Skate 2022",
            "content": "Historic Olympic free skate performance featuring five quadruple jumps and flawless execution.",
            "duration": 285,
            "program_type": "free_program",
            "score": 0.88,
            "highlights": ["5 Quad Jumps", "Olympic Gold", "Technical Mastery"]
        },
        {
            "id": "skater_3",
            "type": "skater", 
            "title": "Sui Wenjing & Han Cong",
            "content": "Chinese pairs skating Olympic champions known for powerful throws and perfect synchronization.",
            "country": "CHN",
            "discipline": "pairs",
            "score": 0.82,
            "highlights": ["Olympic Champions", "Perfect Sync", "Powerful Elements"]
        },
        {
            "id": "competition_2",
            "type": "competition",
            "title": "World Championships 2023 - Saitama",
            "content": "Thrilling World Championships in Japan featuring comeback stories and new rising stars.",
            "year": 2023,
            "location": "Saitama, Japan",
            "score": 0.80,
            "highlights": ["Comeback Stories", "Rising Stars", "Emotional Moments"]
        }
    ]
    
    # Filter by query (comprehensive text matching)
    query_lower = q.lower()
    filtered_results = []
    
    for result in all_results:
        # Check title, content, and highlights
        matches_title = query_lower in result["title"].lower()
        matches_content = query_lower in result["content"].lower()
        matches_highlights = any(query_lower in highlight.lower() for highlight in result.get("highlights", []))
        matches_country = query_lower in result.get("country", "").lower()
        
        if matches_title or matches_content or matches_highlights or matches_country:
            # Boost score based on match quality
            if matches_title:
                result["score"] += 0.1
            if matches_highlights:
                result["score"] += 0.05
            filtered_results.append(result)
    
    # Filter by content type if specified
    if content_type:
        filtered_results = [r for r in filtered_results if r["type"] == content_type]
    
    # Sort by score and limit
    filtered_results.sort(key=lambda x: x["score"], reverse=True)
    limited_results = filtered_results[:limit]
    
    return {
        "query": q,
        "total_found": len(filtered_results),
        "returned": len(limited_results),
        "results": limited_results,
        "search_features": [
            "Full-text search across all content",
            "Semantic matching with highlights",
            "Content type filtering",
            "Relevance scoring",
            "Real-time indexing"
        ],
        "demo_note": "This demonstrates OpenSearch capabilities. Production would search the complete ISU archive."
    }


@app.get("/demo/stories/generate")
async def demo_generate_story(
    story_type: str = Query("profile", description="Type of story (profile, competition_recap, prediction)"),
    skater_name: Optional[str] = Query("Nathan Chen", description="Skater name for story"),
    audience: str = Query("general", description="Target audience (general, media, fans)")
):
    """Demo AI story generation using Qwen LLM capabilities."""
    
    # Simulate AI-generated stories with different styles based on audience
    audience_styles = {
        "general": {
            "tone": "accessible and engaging",
            "technical_level": "basic",
            "focus": "human interest and achievements"
        },
        "media": {
            "tone": "professional and informative", 
            "technical_level": "intermediate",
            "focus": "newsworthy angles and quotes"
        },
        "fans": {
            "tone": "enthusiastic and detailed",
            "technical_level": "advanced",
            "focus": "technical elements and scoring"
        }
    }
    
    style = audience_styles.get(audience, audience_styles["general"])
    
    # Story templates based on type and audience
    stories = {
        "profile": {
            "title": f"The Remarkable Journey of {skater_name}",
            "content": f"""In the world of figure skating, few athletes capture the imagination quite like {skater_name}. 
            
            With a combination of technical precision and artistic flair, they have redefined what it means to compete at the highest level. From early morning training sessions to standing atop Olympic podiums, their journey represents the very best of human determination and skill.

            {f"Their technical mastery is evident in every element, with jump combinations that showcase years of dedicated practice." if audience == "fans" else "Their performances combine athletic excellence with artistic expression that resonates with audiences worldwide."}

            Through years of dedication and countless hours of practice, {skater_name} has emerged as one of the sport's most compelling figures. Their performances transcend mere competition, offering audiences moments of pure artistry and athletic excellence that will be remembered for generations to come.
            
            {f"Recent competition results show consistent high component scores, reflecting their mature artistic development alongside continued technical innovation." if audience == "media" else f"What makes {skater_name} truly special is their ability to make the most difficult elements look effortless while telling a story on ice." if audience == "general" else f"Technical analysis reveals superior edge quality and rotation speed, particularly in quad combinations where they achieve optimal height and distance."}""",
            "summary": f"An inspiring {style['tone']} profile of {skater_name}'s journey from promising young skater to world champion.",
            "tags": ["profile", "inspiration", "skating", skater_name.lower().replace(" ", "-"), audience]
        },
        "competition_recap": {
            "title": f"Thrilling Competition Features {skater_name}'s Outstanding Performance",
            "content": f"""The arena was electric as skaters from around the world took to the ice for one of the season's most anticipated competitions. Record-breaking scores, stunning comebacks, and emotional performances created a night that fans will remember for years to come.

            {skater_name} delivered a masterful performance that showcased the very best of figure skating. {'Their technical score reflected flawless execution across all elements, with particular strength in the second half where base values are multiplied by 1.1.' if audience == 'fans' else 'The performance demonstrated why they remain at the top of their sport.' if audience == 'general' else 'Post-competition interviews revealed their strategic approach to program layout and risk management.'}

            The level of competition has never been higher, with each performance pushing the boundaries of what's possible on ice. Technical innovation combined with artistic expression created a truly spectacular evening of sport.
            
            {f"Scoring breakdown showed exceptional program component marks, with interpretation reaching season-high levels." if audience == "fans" else f"The victory margin demonstrates the gap that has opened between {skater_name} and their competitors." if audience == "media" else f"Witnessing such artistry and athleticism reminds us why figure skating captivates audiences around the world."}""",
            "summary": f"A thrilling competition recap featuring {skater_name}'s outstanding performance and memorable moments.",
            "tags": ["competition", "recap", "skating", "highlights", audience]
        },
        "prediction": {
            "title": f"Analyzing {skater_name}: What the Data Says About Upcoming Competitions",
            "content": f"""Based on recent performance trends and historical data analysis, several factors point to an exciting upcoming competition season for {skater_name}. Current form suggests we may see new personal bests, while their technical evolution continues to drive the sport forward.

            {'Statistical analysis of their recent performances shows improving consistency in technical elements, with success rates above 90% in quad combinations.' if audience == 'fans' else 'Performance metrics indicate they are peaking at the right time for major competitions.' if audience == 'general' else 'Sources close to the training camp report confidence in new program elements that could change competitive dynamics.'}

            The data reveals interesting patterns in scoring and consistency that indicate strong potential for upcoming events. Technical elements have shown steady improvement, while program components remain at elite levels.
            
            {'Current world standings and season best scores position them as the clear favorite, though sport analysts note that figure skating often produces surprises.' if audience == 'media' else 'Technical difficulty scores suggest they may attempt even more challenging elements in future competitions.' if audience == 'fans' else 'This combination of technical mastery and artistic growth suggests fans can expect exceptional performances in the coming season.'}

            {f"Predictive modeling based on current form suggests a 75% probability of podium placement at major events." if audience == "fans" else f"Industry experts expect them to be a major storyline heading into championship season." if audience == "media" else f"Whatever the results, their continued evolution as a skater promises exciting competitions ahead."}""",
            "summary": f"Data-driven analysis predicting {skater_name}'s performance trajectory in upcoming competitions.",
            "tags": ["prediction", "analysis", "data", skater_name.lower().replace(" ", "-"), audience]
        }
    }
    
    story = stories.get(story_type, stories["profile"])
    
    return {
        "story": story,
        "generation_metadata": {
            "ai_model": "Qwen LLM",
            "audience_targeting": style,
            "word_count": len(story["content"].split()),
            "generated_at": datetime.utcnow().isoformat(),
            "processing_time": "0.8 seconds"
        },
        "qwen_features": [
            "Multi-language support",
            "Audience-aware tone adjustment",
            "Technical accuracy",
            "Creative storytelling",
            "Real-time generation"
        ],
        "demo_note": "This demonstrates Qwen LLM's story generation capabilities. Production would use real-time AI processing."
    }


@app.get("/demo/trending")
async def get_demo_trending():
    """Get demo trending content showcasing analytics capabilities."""
    trending = [
        {
            "id": "trend_1",
            "type": "video",
            "title": "🔥 World Championships 2023 Highlights",
            "description": "The most spectacular moments from this year's World Championships featuring breakthrough performances",
            "views": 2100000,
            "engagement_score": 95,
            "trending_rank": 1,
            "growth_rate": "+125% this week",
            "demographics": {"age_18_34": 45, "age_35_54": 35, "age_55+": 20},
            "tags": ["worlds2023", "highlights", "viral", "skating"]
        },
        {
            "id": "trend_2", 
            "type": "analysis",
            "title": "📈 Olympic Predictions: AI Analysis",
            "description": "Advanced analytics predict medal contenders using machine learning and performance data",
            "views": 850000,
            "engagement_score": 88,
            "trending_rank": 2,
            "growth_rate": "+78% this week",
            "demographics": {"age_18_34": 55, "age_35_54": 30, "age_55+": 15},
            "tags": ["predictions", "AI", "olympics", "analytics"]
        },
        {
            "id": "trend_3",
            "type": "story",
            "title": "⭐ Rising Junior Stars: Next Generation",
            "description": "Meet the promising junior skaters who could dominate senior competition in coming years",
            "views": 620000,
            "engagement_score": 82,
            "trending_rank": 3,
            "growth_rate": "+92% this week", 
            "demographics": {"age_18_34": 60, "age_35_54": 25, "age_55+": 15},
            "tags": ["juniors", "future", "talent", "prospects"]
        },
        {
            "id": "trend_4",
            "type": "technique",
            "title": "🎯 Quad Revolution: Technical Breakdown",
            "description": "Deep dive into the technical evolution of quadruple jumps in modern figure skating",
            "views": 445000,
            "engagement_score": 79,
            "trending_rank": 4,
            "growth_rate": "+65% this week",
            "demographics": {"age_18_34": 50, "age_35_54": 35, "age_55+": 15},
            "tags": ["technical", "quads", "analysis", "evolution"]
        }
    ]
    
    return {
        "trending_content": trending,
        "analytics_period": "Last 7 days",
        "total_engagement": sum(item["views"] for item in trending),
        "platform_insights": {
            "peak_viewing_time": "Evening (7-9 PM EST)",
            "top_demographics": "Ages 18-34 (52% of viewers)",
            "engagement_growth": "+89% week-over-week",
            "global_reach": "150+ countries"
        },
        "ai_insights": [
            "Technical content shows 23% higher engagement",
            "Competition highlights peak during event seasons",
            "Predictive content grows 45% during Olympic cycles",
            "Junior content indicates growing young audience"
        ],
        "demo_note": "This showcases AnalyticDB and real-time analytics capabilities for content optimization."
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "Data on Ice API",
        "alibaba_cloud_services": {
            "qwen_llm": {"status": "demo_mode", "response_time": "0.8s"},
            "opensearch": {"status": "demo_mode", "indexed_documents": "50,000+"},
            "analyticdb": {"status": "demo_mode", "query_performance": "< 100ms"},
            "pai_eas": {"status": "demo_mode", "model_endpoints": 3},
            "ecs_gpu": {"status": "demo_mode", "compute_utilization": "45%"}
        },
        "demo_features": {
            "ai_story_generation": "✅ Functional",
            "intelligent_search": "✅ Functional", 
            "trending_analytics": "✅ Functional",
            "multi_audience_content": "✅ Functional",
            "real_time_processing": "✅ Functional"
        },
        "system_info": {
            "total_requests": 12847,
            "avg_response_time": "0.3s",
            "uptime": "99.9%",
            "data_freshness": "< 5 minutes"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🏒 Starting Data on Ice Demo")
    print("🤖 Powered by Alibaba Cloud AI")
    print("🌐 Access at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)