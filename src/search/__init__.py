"""Search functionality using Alibaba OpenSearch."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from opensearchpy import OpenSearch, helpers
from src.config import settings, get_opensearch_config
from src.models import Skater, Competition, Result, Video

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """Client for Alibaba OpenSearch integration."""
    
    def __init__(self):
        self.config = get_opensearch_config()
        self.client = OpenSearch(**self.config)
        self.index_name = settings.opensearch_index
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure the search index exists with proper mapping."""
        if not self.client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},  # skater, competition, result, video
                        "name": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "country": {"type": "keyword"},
                        "discipline": {"type": "keyword"},
                        "bio": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "tags": {"type": "keyword"},
                        "score": {"type": "float"},
                        "position": {"type": "integer"},
                        "year": {"type": "integer"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            
            try:
                self.client.indices.create(
                    index=self.index_name,
                    body=mapping
                )
                logger.info(f"Created OpenSearch index: {self.index_name}")
            except Exception as e:
                logger.error(f"Error creating index: {e}")
    
    async def index_skater(self, skater: Skater) -> bool:
        """Index a skater document."""
        document = {
            "id": f"skater_{skater.id}",
            "type": "skater",
            "name": skater.name,
            "country": skater.country,
            "discipline": skater.discipline,
            "bio": skater.bio or "",
            "content": f"{skater.name} {skater.country} {skater.discipline} {skater.bio or ''}",
            "tags": [skater.country.lower(), skater.discipline.lower() if skater.discipline else ""],
            "created_at": skater.created_at.isoformat() if skater.created_at else datetime.utcnow().isoformat(),
            "updated_at": skater.updated_at.isoformat() if skater.updated_at else datetime.utcnow().isoformat()
        }
        
        try:
            response = self.client.index(
                index=self.index_name,
                id=document["id"],
                body=document
            )
            return response["result"] in ["created", "updated"]
        except Exception as e:
            logger.error(f"Error indexing skater {skater.id}: {e}")
            return False
    
    async def index_competition(self, competition: Competition) -> bool:
        """Index a competition document."""
        document = {
            "id": f"competition_{competition.id}",
            "type": "competition",
            "name": competition.name,
            "year": competition.year,
            "location": competition.location or "",
            "discipline": competition.discipline,
            "level": competition.level,
            "content": f"{competition.name} {competition.year} {competition.location or ''} {competition.discipline or ''}",
            "tags": [
                str(competition.year),
                competition.discipline.lower() if competition.discipline else "",
                competition.level.lower() if competition.level else ""
            ],
            "created_at": competition.created_at.isoformat() if competition.created_at else datetime.utcnow().isoformat()
        }
        
        try:
            response = self.client.index(
                index=self.index_name,
                id=document["id"],
                body=document
            )
            return response["result"] in ["created", "updated"]
        except Exception as e:
            logger.error(f"Error indexing competition {competition.id}: {e}")
            return False
    
    async def index_result(self, result: Result, skater_name: str = None, competition_name: str = None) -> bool:
        """Index a competition result document."""
        document = {
            "id": f"result_{result.id}",
            "type": "result",
            "skater_id": result.skater_id,
            "competition_id": result.competition_id,
            "skater_name": skater_name or "",
            "competition_name": competition_name or "",
            "position": result.position,
            "score": result.total_score,
            "content": f"{skater_name or ''} {competition_name or ''} position {result.position or 'N/A'} score {result.total_score or 'N/A'}",
            "tags": ["result", "competition"],
            "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat()
        }
        
        try:
            response = self.client.index(
                index=self.index_name,
                id=document["id"],
                body=document
            )
            return response["result"] in ["created", "updated"]
        except Exception as e:
            logger.error(f"Error indexing result {result.id}: {e}")
            return False
    
    async def index_video(self, video: Video) -> bool:
        """Index a video document."""
        document = {
            "id": f"video_{video.id}",
            "type": "video",
            "title": video.title,
            "skater_id": video.skater_id,
            "competition_id": video.competition_id,
            "program_type": video.program_type,
            "content": f"{video.title} {video.transcript or ''}",
            "transcript": video.transcript or "",
            "tags": [video.program_type.lower() if video.program_type else "", "video"],
            "created_at": video.created_at.isoformat() if video.created_at else datetime.utcnow().isoformat()
        }
        
        try:
            response = self.client.index(
                index=self.index_name,
                id=document["id"],
                body=document
            )
            return response["result"] in ["created", "updated"]
        except Exception as e:
            logger.error(f"Error indexing video {video.id}: {e}")
            return False
    
    async def search(self, query: str, 
                    filters: Dict[str, Any] = None,
                    size: int = 20,
                    from_: int = 0) -> Dict[str, Any]:
        """Perform search across all content."""
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "content^2", "bio", "transcript"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "content": {},
                    "bio": {},
                    "transcript": {}
                }
            },
            "size": size,
            "from": from_
        }
        
        # Apply filters
        if filters:
            filter_clauses = []
            
            if "type" in filters:
                filter_clauses.append({"term": {"type": filters["type"]}})
            
            if "country" in filters:
                filter_clauses.append({"term": {"country": filters["country"]}})
            
            if "discipline" in filters:
                filter_clauses.append({"term": {"discipline": filters["discipline"]}})
            
            if "year_range" in filters:
                year_range = filters["year_range"]
                filter_clauses.append({
                    "range": {
                        "year": {
                            "gte": year_range.get("from"),
                            "lte": year_range.get("to")
                        }
                    }
                })
            
            if filter_clauses:
                search_body["query"]["bool"]["filter"] = filter_clauses
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            return response
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}
    
    async def search_skaters(self, query: str, 
                           country: str = None,
                           discipline: str = None,
                           size: int = 10) -> List[Dict[str, Any]]:
        """Search specifically for skaters."""
        filters = {"type": "skater"}
        if country:
            filters["country"] = country
        if discipline:
            filters["discipline"] = discipline
        
        response = await self.search(query, filters, size)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def search_competitions(self, query: str,
                                year: int = None,
                                discipline: str = None,
                                size: int = 10) -> List[Dict[str, Any]]:
        """Search specifically for competitions."""
        filters = {"type": "competition"}
        if discipline:
            filters["discipline"] = discipline
        if year:
            filters["year_range"] = {"from": year, "to": year}
        
        response = await self.search(query, filters, size)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def search_videos(self, query: str,
                          program_type: str = None,
                          size: int = 10) -> List[Dict[str, Any]]:
        """Search specifically for videos."""
        filters = {"type": "video"}
        
        response = await self.search(query, filters, size)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def get_recommendations(self, skater_id: int, size: int = 5) -> List[Dict[str, Any]]:
        """Get content recommendations based on a skater."""
        # Find similar skaters based on discipline and country
        search_body = {
            "query": {
                "more_like_this": {
                    "fields": ["content", "discipline", "country"],
                    "like": [
                        {
                            "_index": self.index_name,
                            "_id": f"skater_{skater_id}"
                        }
                    ],
                    "min_term_freq": 1,
                    "max_query_terms": 12
                }
            },
            "size": size
        }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return []
    
    async def get_trending_content(self, days: int = 30, size: int = 10) -> List[Dict[str, Any]]:
        """Get trending content based on recent activity."""
        # For demo purposes, return recent content
        # In production, this would use actual engagement metrics
        search_body = {
            "query": {
                "range": {
                    "created_at": {
                        "gte": f"now-{days}d"
                    }
                }
            },
            "sort": [
                {"created_at": {"order": "desc"}}
            ],
            "size": size
        }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Trending content error: {e}")
            return []
    
    async def bulk_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents."""
        actions = []
        for doc in documents:
            action = {
                "_index": self.index_name,
                "_id": doc["id"],
                "_source": doc
            }
            actions.append(action)
        
        try:
            helpers.bulk(self.client, actions)
            logger.info(f"Bulk indexed {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Bulk index error: {e}")
            return False


class SearchService:
    """High-level search service."""
    
    def __init__(self):
        self.client = OpenSearchClient()
    
    async def unified_search(self, query: str, 
                           content_types: List[str] = None,
                           filters: Dict[str, Any] = None,
                           page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        """Unified search across all content types."""
        from_ = (page - 1) * page_size
        
        # If specific content types requested, filter by them
        if content_types:
            if not filters:
                filters = {}
            # Note: This would need to be adapted for multiple content types
            # For now, we'll search all and filter in post-processing
        
        response = await self.client.search(query, filters, page_size, from_)
        
        # Group results by content type
        results_by_type = {
            "skaters": [],
            "competitions": [],
            "results": [],
            "videos": []
        }
        
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            content_type = source.get("type")
            
            if content_type == "skater":
                results_by_type["skaters"].append(source)
            elif content_type == "competition":
                results_by_type["competitions"].append(source)
            elif content_type == "result":
                results_by_type["results"].append(source)
            elif content_type == "video":
                results_by_type["videos"].append(source)
        
        return {
            "query": query,
            "total": response["hits"]["total"]["value"],
            "page": page,
            "page_size": page_size,
            "results": results_by_type,
            "facets": await self._get_search_facets(query, filters)
        }
    
    async def _get_search_facets(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get search facets for filtering."""
        # Simplified facets - in production this would be more comprehensive
        return {
            "content_types": ["skater", "competition", "result", "video"],
            "disciplines": ["singles", "pairs", "ice_dance"],
            "countries": ["USA", "RUS", "JPN", "CAN", "CHN"]  # This would be dynamic
        }