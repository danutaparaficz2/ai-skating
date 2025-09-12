"""AI processing module using Alibaba Qwen LLM for story generation."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import requests
from transformers import pipeline
from src.config import settings
from src.models import Skater, Competition, Result, Video, StoryRequest, StoryResponse

logger = logging.getLogger(__name__)


class QwenLLMClient:
    """Client for Alibaba Qwen LLM API."""
    
    def __init__(self):
        self.api_key = settings.qwen_api_key
        self.model_name = settings.qwen_model_name
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_story(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate story content using Qwen LLM."""
        try:
            payload = {
                "model": self.model_name,
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert sports journalist specializing in figure skating. Create engaging, accurate, and personalized content for skating fans."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                "parameters": {
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["output"]["text"]
            else:
                logger.error(f"Qwen API error: {response.status_code} - {response.text}")
                return self._fallback_generation(prompt)
                
        except Exception as e:
            logger.error(f"Error calling Qwen API: {e}")
            return self._fallback_generation(prompt)
    
    def _fallback_generation(self, prompt: str) -> str:
        """Fallback text generation when Qwen API is unavailable."""
        # Simple fallback for demo purposes
        return f"Generated story based on: {prompt[:100]}..."


class StoryGenerator:
    """Generates personalized stories from skating data."""
    
    def __init__(self):
        self.qwen_client = QwenLLMClient()
        self.sentiment_analyzer = None
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                             model="distilbert-base-uncased-finetuned-sst-2-english")
        except Exception as e:
            logger.warning(f"Could not load sentiment analyzer: {e}")
    
    async def generate_skater_profile(self, skater: Skater, 
                                    results: List[Result] = None,
                                    videos: List[Video] = None,
                                    audience: str = "general") -> StoryResponse:
        """Generate a personalized skater profile story."""
        
        # Build context from available data
        context = self._build_skater_context(skater, results, videos)
        
        # Create prompt based on audience
        prompt = self._create_profile_prompt(context, audience)
        
        # Generate story using Qwen LLM
        content = await self.qwen_client.generate_story(prompt)
        
        # Generate title and summary
        title = await self._generate_title(content, "profile")
        summary = await self._generate_summary(content)
        
        # Extract tags
        tags = self._extract_tags(skater, results)
        
        return StoryResponse(
            title=title,
            content=content,
            summary=summary,
            tags=tags,
            related_videos=videos or [],
            related_results=results or [],
            generated_at=datetime.utcnow()
        )
    
    async def generate_competition_recap(self, competition: Competition,
                                       results: List[Result],
                                       videos: List[Video] = None,
                                       audience: str = "general") -> StoryResponse:
        """Generate a competition recap story."""
        
        context = self._build_competition_context(competition, results, videos)
        prompt = self._create_recap_prompt(context, audience)
        
        content = await self.qwen_client.generate_story(prompt, max_tokens=1500)
        title = await self._generate_title(content, "recap")
        summary = await self._generate_summary(content)
        tags = self._extract_competition_tags(competition, results)
        
        return StoryResponse(
            title=title,
            content=content,
            summary=summary,
            tags=tags,
            related_videos=videos or [],
            related_results=results,
            generated_at=datetime.utcnow()
        )
    
    async def generate_prediction(self, skater: Skater,
                                historical_results: List[Result],
                                upcoming_competition: str,
                                audience: str = "general") -> StoryResponse:
        """Generate a predictive story about skater's performance."""
        
        context = self._build_prediction_context(skater, historical_results, upcoming_competition)
        prompt = self._create_prediction_prompt(context, audience)
        
        content = await self.qwen_client.generate_story(prompt, max_tokens=800)
        title = await self._generate_title(content, "prediction")
        summary = await self._generate_summary(content)
        tags = ["prediction", "analysis", skater.name.lower().replace(" ", "-")]
        
        return StoryResponse(
            title=title,
            content=content,
            summary=summary,
            tags=tags,
            related_videos=[],
            related_results=historical_results,
            generated_at=datetime.utcnow()
        )
    
    def _build_skater_context(self, skater: Skater, 
                            results: List[Result] = None,
                            videos: List[Video] = None) -> Dict[str, Any]:
        """Build context data for skater profile generation."""
        context = {
            "name": skater.name,
            "country": skater.country,
            "discipline": skater.discipline,
            "bio": skater.bio or "",
            "achievements": skater.achievements or {}
        }
        
        if results:
            # Analyze performance trends
            scores = [r.total_score for r in results if r.total_score]
            if scores:
                context["avg_score"] = sum(scores) / len(scores)
                context["best_score"] = max(scores)
                context["recent_trend"] = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
            
            # Competition history
            context["competitions"] = len(results)
            context["podium_finishes"] = len([r for r in results if r.position and r.position <= 3])
        
        if videos:
            context["video_count"] = len(videos)
            context["recent_performances"] = [v.title for v in videos[:3]]
        
        return context
    
    def _build_competition_context(self, competition: Competition,
                                 results: List[Result],
                                 videos: List[Video] = None) -> Dict[str, Any]:
        """Build context for competition recap."""
        context = {
            "competition_name": competition.name,
            "year": competition.year,
            "location": competition.location,
            "discipline": competition.discipline,
            "level": competition.level
        }
        
        if results:
            # Sort results by position
            sorted_results = sorted([r for r in results if r.position], 
                                  key=lambda x: x.position)
            
            context["winner"] = sorted_results[0] if sorted_results else None
            context["podium"] = sorted_results[:3] if len(sorted_results) >= 3 else sorted_results
            context["total_participants"] = len(results)
            
            # Performance statistics
            scores = [r.total_score for r in results if r.total_score]
            if scores:
                context["highest_score"] = max(scores)
                context["avg_score"] = sum(scores) / len(scores)
        
        return context
    
    def _build_prediction_context(self, skater: Skater,
                                historical_results: List[Result],
                                upcoming_competition: str) -> Dict[str, Any]:
        """Build context for prediction generation."""
        context = {
            "skater_name": skater.name,
            "country": skater.country,
            "discipline": skater.discipline,
            "upcoming_competition": upcoming_competition
        }
        
        if historical_results:
            scores = [r.total_score for r in historical_results if r.total_score]
            positions = [r.position for r in historical_results if r.position]
            
            if scores:
                context["recent_scores"] = scores[-5:]  # Last 5 competitions
                context["score_trend"] = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
                context["avg_score"] = sum(scores) / len(scores)
            
            if positions:
                context["recent_positions"] = positions[-5:]
                context["avg_position"] = sum(positions) / len(positions)
                context["best_position"] = min(positions)
        
        return context
    
    def _create_profile_prompt(self, context: Dict[str, Any], audience: str) -> str:
        """Create prompt for skater profile generation."""
        base_prompt = f"""
        Write an engaging profile about figure skater {context['name']} from {context['country']}.
        
        Background information:
        - Discipline: {context.get('discipline', 'Unknown')}
        - Bio: {context.get('bio', 'No bio available')}
        - Achievements: {json.dumps(context.get('achievements', {}), indent=2)}
        """
        
        if context.get('competitions'):
            base_prompt += f"""
            
            Performance Statistics:
            - Competitions: {context['competitions']}
            - Podium finishes: {context.get('podium_finishes', 0)}
            - Average score: {context.get('avg_score', 'N/A')}
            - Best score: {context.get('best_score', 'N/A')}
            - Recent trend: {context.get('recent_trend', 'N/A')}
            """
        
        audience_instructions = {
            "general": "Write for general sports fans who may not know technical skating terms.",
            "media": "Write for sports journalists and media professionals with skating knowledge.",
            "fans": "Write for dedicated figure skating fans who understand technical elements."
        }
        
        base_prompt += f"\n\nAudience: {audience_instructions.get(audience, audience_instructions['general'])}"
        base_prompt += "\n\nWrite a compelling 2-3 paragraph story that captures the skater's journey, personality, and achievements."
        
        return base_prompt
    
    def _create_recap_prompt(self, context: Dict[str, Any], audience: str) -> str:
        """Create prompt for competition recap."""
        prompt = f"""
        Write an exciting recap of the {context['competition_name']} {context['year']} competition.
        
        Competition Details:
        - Location: {context.get('location', 'Unknown')}
        - Discipline: {context.get('discipline', 'Unknown')}
        - Level: {context.get('level', 'Unknown')}
        - Total participants: {context.get('total_participants', 'Unknown')}
        """
        
        if context.get('podium'):
            prompt += "\n\nPodium Results:\n"
            for i, result in enumerate(context['podium'], 1):
                prompt += f"{i}. Position {result.position} - Score: {result.total_score}\n"
        
        prompt += f"\n\nWrite an engaging 3-4 paragraph recap focusing on the highlights, drama, and standout performances."
        
        return prompt
    
    def _create_prediction_prompt(self, context: Dict[str, Any], audience: str) -> str:
        """Create prompt for prediction story."""
        prompt = f"""
        Analyze {context['skater_name']} from {context['country']}'s chances at the upcoming {context['upcoming_competition']}.
        
        Recent Performance Data:
        - Recent scores: {context.get('recent_scores', [])}
        - Score trend: {context.get('score_trend', 'Unknown')}
        - Average score: {context.get('avg_score', 'N/A')}
        - Recent positions: {context.get('recent_positions', [])}
        - Best position: {context.get('best_position', 'N/A')}
        
        Write a thoughtful analysis predicting their performance based on recent trends and form.
        """
        
        return prompt
    
    async def _generate_title(self, content: str, story_type: str) -> str:
        """Generate an engaging title for the story."""
        title_prompt = f"Generate a compelling headline for this {story_type} story: {content[:200]}..."
        title = await self.qwen_client.generate_story(title_prompt, max_tokens=50)
        return title.strip().replace('"', '').replace('\n', ' ')[:100]
    
    async def _generate_summary(self, content: str) -> str:
        """Generate a brief summary of the story."""
        summary_prompt = f"Write a 1-2 sentence summary of this story: {content}"
        summary = await self.qwen_client.generate_story(summary_prompt, max_tokens=100)
        return summary.strip()
    
    def _extract_tags(self, skater: Skater, results: List[Result] = None) -> List[str]:
        """Extract relevant tags for the story."""
        tags = [
            skater.name.lower().replace(" ", "-"),
            skater.country.lower(),
            skater.discipline.lower() if skater.discipline else "skating"
        ]
        
        if results:
            if any(r.position and r.position == 1 for r in results):
                tags.append("champion")
            if any(r.position and r.position <= 3 for r in results):
                tags.append("medalist")
        
        return list(set(tags))
    
    def _extract_competition_tags(self, competition: Competition, results: List[Result]) -> List[str]:
        """Extract tags for competition stories."""
        tags = [
            competition.name.lower().replace(" ", "-"),
            str(competition.year),
            competition.discipline.lower() if competition.discipline else "skating",
            "competition",
            "recap"
        ]
        
        if competition.location:
            tags.append(competition.location.lower().replace(" ", "-"))
        
        return list(set(tags))