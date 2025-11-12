"""
Certifications API Routes for WWMAA Backend

Provides public endpoints for accessing available martial arts certifications.

Endpoints:
- GET /api/certifications: List all available certifications
- GET /api/certifications/{id}: Get single certification by ID

Features:
- Hardcoded certification data
- Public endpoints (no authentication required)
- Proper error handling and logging
- Pydantic models for data validation
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/certifications",
    tags=["certifications"]
)


# Pydantic Models
class Certification(BaseModel):
    """Certification data model"""
    id: str = Field(..., description="Unique certification identifier")
    name: str = Field(..., description="Certification name")
    description: str = Field(..., description="Detailed certification description")
    requirements: Optional[List[str]] = Field(None, description="List of certification requirements")
    duration: Optional[str] = Field(None, description="Certification duration/validity period")
    level: Optional[str] = Field(None, description="Certification level (Beginner, Intermediate, Advanced)")


class CertificationListResponse(BaseModel):
    """Response model for certification list endpoint"""
    data: List[Certification]
    total: int


# Hardcoded certification data
CERTIFICATIONS_DATA = [
    {
        "id": "cert_judo_instructor",
        "name": "Judo Instructor",
        "description": "Comprehensive instructor certification for teaching traditional Judo techniques, emphasizing throws, grappling, and the philosophical principles of maximum efficiency and mutual welfare. Suitable for practitioners seeking to guide students in Judo practice and competition.",
        "requirements": [
            "Minimum 2nd Dan black belt in Judo",
            "At least 5 years of active Judo practice",
            "Complete 40-hour instructor training course",
            "Pass written examination on Judo history and technique",
            "Demonstrate teaching proficiency in practical evaluation",
            "Current CPR and First Aid certification"
        ],
        "duration": "3 years (renewable)",
        "level": "Advanced"
    },
    {
        "id": "cert_karate_instructor",
        "name": "Karate Instructor",
        "description": "Professional certification for teaching Karate, covering kata, kumite, and fundamental striking techniques. This certification prepares instructors to teach students of all ages and skill levels, with emphasis on discipline, respect, and technical excellence.",
        "requirements": [
            "Minimum 2nd Dan black belt in recognized Karate style",
            "At least 4 years of teaching experience under supervision",
            "Complete 35-hour instructor certification program",
            "Demonstrate proficiency in all basic and intermediate kata",
            "Pass practical and written examinations",
            "Background check clearance",
            "Current CPR and First Aid certification"
        ],
        "duration": "3 years (renewable)",
        "level": "Advanced"
    },
    {
        "id": "cert_self_defense_instructor",
        "name": "Self-Defense Instructor",
        "description": "Specialized certification focusing on practical self-defense techniques, situational awareness, and de-escalation strategies. Designed for instructors teaching women's self-defense, personal safety, and conflict avoidance in real-world scenarios.",
        "requirements": [
            "Minimum 1st Dan black belt in any martial art OR 3+ years of verified self-defense training",
            "Complete 30-hour self-defense instructor course",
            "Demonstrate proficiency in teaching practical defense scenarios",
            "Pass written exam on legal aspects of self-defense",
            "Complete trauma-informed teaching training",
            "Current CPR and First Aid certification"
        ],
        "duration": "2 years (renewable)",
        "level": "Intermediate"
    },
    {
        "id": "cert_tournament_official",
        "name": "Tournament Official",
        "description": "Certification for judging and officiating martial arts competitions and tournaments. Covers scoring systems, rules enforcement, safety protocols, and ethical officiating standards across multiple martial arts disciplines.",
        "requirements": [
            "Minimum 1st Dan black belt in any martial art",
            "At least 2 years of competitive experience",
            "Complete 20-hour tournament official training",
            "Shadow experienced officials at 3 sanctioned tournaments",
            "Pass written rules and regulations examination",
            "Demonstrate knowledge of multiple competition formats"
        ],
        "duration": "2 years (renewable)",
        "level": "Intermediate"
    }
]


@router.get("", response_model=CertificationListResponse)
async def list_certifications(
    level: Optional[str] = Query(None, description="Filter by certification level (Beginner, Intermediate, Advanced)")
):
    """
    List all available certifications

    Returns a list of all martial arts certifications offered by WWMAA.
    Optionally filter by certification level.

    Args:
        level: Filter by certification level (optional)

    Returns:
        List of certification objects with id, name, description, requirements, duration, and level
    """
    try:
        logger.info(f"Fetching certifications list: level={level}")

        # Get all certifications
        certifications = CERTIFICATIONS_DATA.copy()

        # Apply level filter if provided
        if level:
            certifications = [
                cert for cert in certifications
                if cert.get('level', '').lower() == level.lower()
            ]
            logger.info(f"Filtered certifications by level '{level}': {len(certifications)} results")

        logger.info(f"Returning {len(certifications)} certifications")

        return {
            "data": certifications,
            "total": len(certifications)
        }

    except Exception as e:
        logger.error(f"Error fetching certifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch certifications"
        )


@router.get("/{certification_id}", response_model=Certification)
async def get_certification_by_id(certification_id: str):
    """
    Get a single certification by ID

    Args:
        certification_id: Unique certification identifier

    Returns:
        Certification data with full details

    Raises:
        HTTPException: If certification not found (404)
    """
    try:
        logger.info(f"Fetching certification by ID: {certification_id}")

        # Find certification by ID
        certification = next(
            (cert for cert in CERTIFICATIONS_DATA if cert["id"] == certification_id),
            None
        )

        if not certification:
            logger.warning(f"Certification not found: {certification_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Certification with ID '{certification_id}' not found"
            )

        logger.info(f"Found certification: {certification['name']}")
        return certification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching certification {certification_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch certification"
        )


@router.get("/search/by-name")
async def search_certifications_by_name(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)")
):
    """
    Search certifications by name

    Performs case-insensitive search on certification names.

    Args:
        q: Search query string (minimum 2 characters)

    Returns:
        List of matching certifications
    """
    try:
        logger.info(f"Searching certifications by name: query='{q}'")

        # Perform case-insensitive search
        query_lower = q.lower()
        results = [
            cert for cert in CERTIFICATIONS_DATA
            if query_lower in cert["name"].lower() or query_lower in cert["description"].lower()
        ]

        logger.info(f"Found {len(results)} certifications matching query '{q}'")

        return {
            "data": results,
            "total": len(results),
            "query": q
        }

    except Exception as e:
        logger.error(f"Error searching certifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to search certifications"
        )


@router.get("/levels/list")
async def list_certification_levels():
    """
    List all available certification levels

    Returns unique certification levels with counts.

    Returns:
        List of certification levels with counts
    """
    try:
        logger.info("Fetching certification levels")

        # Extract unique levels with counts
        level_counts = {}
        for cert in CERTIFICATIONS_DATA:
            level = cert.get("level")
            if level:
                level_counts[level] = level_counts.get(level, 0) + 1

        # Format response
        levels = [
            {
                "name": level,
                "count": count
            }
            for level, count in sorted(level_counts.items())
        ]

        logger.info(f"Returning {len(levels)} certification levels")

        return {
            "data": levels,
            "total": len(levels)
        }

    except Exception as e:
        logger.error(f"Error fetching certification levels: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch certification levels"
        )
