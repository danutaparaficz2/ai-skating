"""Utility functions for the Data on Ice project."""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


def generate_sample_data():
    """Generate sample ISU skating data for testing."""
    
    # Sample skaters
    skaters = [
        {
            "name": "Yuzuru Hanyu",
            "country": "JPN",
            "birth_date": "1994-12-07",
            "discipline": "singles",
            "bio": "Two-time Olympic champion known for his artistic expression and technical mastery.",
            "achievements": {
                "olympic_gold": 2,
                "world_championships": 2,
                "grand_prix_finals": 4
            }
        },
        {
            "name": "Nathan Chen",
            "country": "USA", 
            "birth_date": "1999-05-05",
            "discipline": "singles",
            "bio": "American figure skater known for his quadruple jumps and consistency.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 3,
                "grand_prix_finals": 1
            }
        },
        {
            "name": "Sui Wenjing",
            "country": "CHN",
            "birth_date": "1995-07-18", 
            "discipline": "pairs",
            "bio": "Chinese pairs skater, Olympic champion with partner Han Cong.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 2,
                "grand_prix_finals": 2
            }
        },
        {
            "name": "Gabriella Papadakis",
            "country": "FRA",
            "birth_date": "1995-05-10",
            "discipline": "ice_dance", 
            "bio": "French ice dancer, Olympic champion with partner Guillaume Cizeron.",
            "achievements": {
                "olympic_gold": 1,
                "world_championships": 5,
                "grand_prix_finals": 4
            }
        }
    ]
    
    # Sample competitions
    competitions = [
        {
            "name": "Winter Olympics",
            "year": 2022,
            "location": "Beijing, China",
            "start_date": "2022-02-04",
            "end_date": "2022-02-20",
            "discipline": "singles",
            "level": "senior"
        },
        {
            "name": "World Championships",
            "year": 2023,
            "location": "Saitama, Japan", 
            "start_date": "2023-03-20",
            "end_date": "2023-03-26",
            "discipline": "singles",
            "level": "senior"
        },
        {
            "name": "Grand Prix Final",
            "year": 2023,
            "location": "Turin, Italy",
            "start_date": "2023-12-07",
            "end_date": "2023-12-10",
            "discipline": "singles", 
            "level": "senior"
        }
    ]
    
    # Sample results
    results = [
        {
            "skater": {"name": "Nathan Chen", "country": "USA"},
            "competition": {"name": "Winter Olympics", "year": 2022},
            "position": 1,
            "total_score": 332.60,
            "short_program_score": 113.97,
            "free_program_score": 218.63,
            "technical_score": 182.83,
            "component_score": 149.77,
            "deductions": 0.0,
            "video_url": "https://example.com/video1"
        },
        {
            "skater": {"name": "Yuzuru Hanyu", "country": "JPN"},
            "competition": {"name": "Winter Olympics", "year": 2022},
            "position": 4,
            "total_score": 283.21,
            "short_program_score": 95.15,
            "free_program_score": 188.06,
            "technical_score": 154.32,
            "component_score": 128.89,
            "deductions": 0.0,
            "video_url": "https://example.com/video2"
        }
    ]
    
    # Sample videos
    videos = [
        {
            "title": "Nathan Chen - Olympic Free Skate 2022",
            "url": "https://example.com/video1",
            "thumbnail_url": "https://example.com/thumb1.jpg",
            "duration": 285,
            "skater_id": 1,
            "competition_id": 1,
            "program_type": "free_program",
            "transcript": "Nathan Chen performs his Olympic free skate with five quadruple jumps...",
            "metadata": {"views": 1000000, "likes": 50000}
        },
        {
            "title": "Yuzuru Hanyu - Olympic Short Program 2022", 
            "url": "https://example.com/video2",
            "thumbnail_url": "https://example.com/thumb2.jpg",
            "duration": 175,
            "skater_id": 2,
            "competition_id": 1,
            "program_type": "short_program",
            "transcript": "Yuzuru Hanyu's emotional short program performance at his final Olympics...",
            "metadata": {"views": 2000000, "likes": 100000}
        }
    ]
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Save sample data
    with open(data_dir / "sample_skaters.json", "w") as f:
        json.dump(skaters, f, indent=2)
    
    with open(data_dir / "sample_competitions.json", "w") as f:
        json.dump(competitions, f, indent=2)
        
    with open(data_dir / "sample_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    with open(data_dir / "sample_videos.json", "w") as f:
        json.dump(videos, f, indent=2)
    
    print("Sample data generated in data/ directory")
    return {
        "skaters": len(skaters),
        "competitions": len(competitions), 
        "results": len(results),
        "videos": len(videos)
    }


def format_score(score: float) -> str:
    """Format skating score for display."""
    return f"{score:.2f}" if score else "N/A"


def format_position(position: int) -> str:
    """Format competition position with ordinal suffix."""
    if not position:
        return "N/A"
    
    if 10 <= position % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(position % 10, "th")
    
    return f"{position}{suffix}"


def calculate_age(birth_date: datetime, reference_date: datetime = None) -> int:
    """Calculate age from birth date."""
    if not birth_date:
        return None
    
    if not reference_date:
        reference_date = datetime.utcnow()
    
    age = reference_date.year - birth_date.year
    if reference_date.month < birth_date.month or \
       (reference_date.month == birth_date.month and reference_date.day < birth_date.day):
        age -= 1
    
    return age


def extract_highlights(text: str, max_length: int = 200) -> str:
    """Extract highlights from text content."""
    if not text or len(text) <= max_length:
        return text
    
    # Find sentence boundaries
    sentences = text.split('. ')
    result = ""
    
    for sentence in sentences:
        if len(result + sentence) <= max_length - 3:
            result += sentence + ". "
        else:
            break
    
    if len(result) < max_length - 3:
        result += "..."
    
    return result.strip()


def generate_seo_keywords(skater_name: str, competition_name: str = None, 
                         discipline: str = None) -> List[str]:
    """Generate SEO keywords for content."""
    keywords = [
        skater_name.lower(),
        "figure skating",
        "ice skating"
    ]
    
    if competition_name:
        keywords.extend([
            competition_name.lower(),
            "competition",
            "results"
        ])
    
    if discipline:
        keywords.append(discipline.lower())
    
    # Add common skating terms
    keywords.extend([
        "olympics",
        "world championships", 
        "skating performance",
        "ice sports"
    ])
    
    return list(set(keywords))


def validate_score_range(score: float, min_score: float = 0.0, max_score: float = 500.0) -> bool:
    """Validate if a skating score is within reasonable range."""
    return min_score <= score <= max_score if score is not None else True


def get_discipline_info(discipline: str) -> Dict[str, Any]:
    """Get information about skating disciplines."""
    disciplines = {
        "singles": {
            "name": "Men's/Women's Singles",
            "description": "Individual skating with jumps, spins, and step sequences",
            "typical_duration": {"short": 170, "free": 270}
        },
        "pairs": {
            "name": "Pairs Skating", 
            "description": "Two skaters performing together with lifts, throws, and synchronized elements",
            "typical_duration": {"short": 170, "free": 270}
        },
        "ice_dance": {
            "name": "Ice Dance",
            "description": "Dance-focused skating emphasizing rhythm, interpretation, and partnerships", 
            "typical_duration": {"rhythm": 170, "free": 250}
        }
    }
    
    return disciplines.get(discipline.lower(), {
        "name": discipline.title(),
        "description": "Figure skating discipline",
        "typical_duration": {"short": 170, "free": 270}
    })


if __name__ == "__main__":
    # Generate sample data when run directly
    stats = generate_sample_data()
    print(f"Generated sample data: {stats}")