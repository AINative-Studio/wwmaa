"""
Sample Vector Test Data

Provides mock embeddings and content samples for testing vector search functionality.
These are realistic mock vectors that simulate OpenAI text-embedding-ada-002 outputs.
"""

import numpy as np
from typing import List, Dict, Any
from uuid import uuid4


def generate_mock_embedding(seed: int, dimension: int = 1536) -> List[float]:
    """
    Generate a normalized mock embedding vector

    Args:
        seed: Random seed for reproducibility
        dimension: Vector dimension (default: 1536 for OpenAI ada-002)

    Returns:
        Normalized vector as list of floats
    """
    np.random.seed(seed)
    vector = np.random.randn(dimension)
    # Normalize to unit length (as real embeddings are)
    magnitude = np.linalg.norm(vector)
    return (vector / magnitude).tolist()


def create_similar_embedding(base_embedding: List[float], similarity: float = 0.9) -> List[float]:
    """
    Create a vector similar to the base embedding

    Args:
        base_embedding: Base vector
        similarity: Target cosine similarity (0-1)

    Returns:
        Similar vector with approximately the target similarity
    """
    base = np.array(base_embedding)
    # Generate random noise
    noise = np.random.randn(len(base))
    noise = noise / np.linalg.norm(noise)

    # Mix base and noise to achieve target similarity
    # similarity = cos(theta), so theta = arccos(similarity)
    theta = np.arccos(np.clip(similarity, -1, 1))
    weight = np.cos(theta)
    noise_weight = np.sin(theta)

    similar = weight * base + noise_weight * noise
    # Normalize
    similar = similar / np.linalg.norm(similar)

    return similar.tolist()


# ============================================================================
# SAMPLE EMBEDDINGS
# ============================================================================

SAMPLE_EMBEDDINGS = {
    # Event-related embeddings
    "event_karate_tournament": generate_mock_embedding(100),
    "event_taekwondo_seminar": generate_mock_embedding(101),
    "event_judo_competition": generate_mock_embedding(102),
    "event_mma_training": generate_mock_embedding(103),

    # Article-related embeddings
    "article_karate_history": generate_mock_embedding(200),
    "article_taekwondo_techniques": generate_mock_embedding(201),
    "article_belt_ranking": generate_mock_embedding(202),
    "article_meditation": generate_mock_embedding(203),

    # Profile-related embeddings
    "profile_karate_instructor": generate_mock_embedding(300),
    "profile_judo_master": generate_mock_embedding(301),
    "profile_mma_coach": generate_mock_embedding(302),

    # Video-related embeddings
    "video_kata_tutorial": generate_mock_embedding(400),
    "video_sparring_tips": generate_mock_embedding(401),
    "video_conditioning": generate_mock_embedding(402),

    # Query embeddings (for search testing)
    "query_tournament_near_me": generate_mock_embedding(500),
    "query_beginner_classes": generate_mock_embedding(501),
    "query_black_belt_requirements": generate_mock_embedding(502),
    "query_martial_arts_history": generate_mock_embedding(503),
}


# ============================================================================
# SAMPLE CONTENT METADATA
# ============================================================================

SAMPLE_CONTENT = [
    {
        "id": str(uuid4()),
        "source_type": "event",
        "source_id": str(uuid4()),
        "url": "https://wwmaa.com/events/la-karate-championship",
        "title": "Los Angeles Karate Championship 2024",
        "content_chunk": (
            "Join us for the premier karate tournament in Los Angeles. "
            "This annual championship features black belt competitors from across "
            "California competing in kata and kumite divisions. Open to all karate "
            "styles including Shotokan, Goju-Ryu, and Shito-Ryu. Registration "
            "deadline is December 1st. Event includes junior, adult, and senior "
            "divisions with cash prizes for winners."
        ),
        "embedding": SAMPLE_EMBEDDINGS["event_karate_tournament"],
        "metadata": {
            "location": "Los Angeles, CA",
            "event_date": "2024-12-15",
            "event_type": "tournament",
            "disciplines": ["karate"],
            "skill_level": "black_belt"
        },
        "tags": ["tournament", "karate", "los-angeles", "competition", "championship"],
        "visibility": "public",
        "search_weight": 2.0,
        "is_active": True
    },
    {
        "id": str(uuid4()),
        "source_type": "event",
        "source_id": str(uuid4()),
        "url": "https://wwmaa.com/events/taekwondo-seminar",
        "title": "Master Kim's Taekwondo Technique Seminar",
        "content_chunk": (
            "World-renowned Master Kim will conduct a special seminar on advanced "
            "taekwondo kicking techniques. Learn jumping kicks, spinning kicks, and "
            "combination techniques from a 7th degree black belt with Olympic coaching "
            "experience. Suitable for intermediate and advanced practitioners. "
            "Limited to 50 participants. Includes hands-on training and Q&A session."
        ),
        "embedding": SAMPLE_EMBEDDINGS["event_taekwondo_seminar"],
        "metadata": {
            "location": "San Francisco, CA",
            "event_date": "2024-11-20",
            "event_type": "seminar",
            "disciplines": ["taekwondo"],
            "skill_level": "intermediate_advanced",
            "instructor": "Master Kim"
        },
        "tags": ["seminar", "taekwondo", "san-francisco", "techniques", "master-class"],
        "visibility": "public",
        "search_weight": 1.8,
        "is_active": True
    },
    {
        "id": str(uuid4()),
        "source_type": "article",
        "source_id": str(uuid4()),
        "url": "https://wwmaa.com/articles/history-of-taekwondo",
        "title": "The Evolution of Taekwondo: From Ancient Korea to Modern Sport",
        "content_chunk": (
            "Taekwondo is a Korean martial art characterized by its emphasis on "
            "head-height kicks, jumping and spinning kicks, and fast kicking techniques. "
            "The name taekwondo was officially adopted in 1955, but its roots trace back "
            "to ancient Korean martial arts including Taekkyeon and Subak. This article "
            "explores how taekwondo evolved from traditional Korean combat methods to "
            "become an Olympic sport, examining the influence of Japanese martial arts "
            "during the occupation period and the subsequent effort to reclaim Korean "
            "martial heritage."
        ),
        "embedding": SAMPLE_EMBEDDINGS["article_taekwondo_techniques"],
        "metadata": {
            "category": "history",
            "publish_date": "2024-10-15",
            "author": "Dr. Sarah Chen",
            "reading_time": "8 minutes",
            "difficulty": "beginner"
        },
        "tags": ["history", "taekwondo", "education", "korean-martial-arts", "olympics"],
        "visibility": "public",
        "search_weight": 1.5,
        "is_active": True
    },
    {
        "id": str(uuid4()),
        "source_type": "profile",
        "source_id": str(uuid4()),
        "url": "https://wwmaa.com/profiles/john-smith",
        "title": "Master John Smith - 5th Degree Judo Black Belt",
        "content_chunk": (
            "Master John Smith is a 5th degree black belt (Godan) in Judo with over "
            "30 years of teaching and competition experience. He began his judo journey "
            "at age 12 and earned his black belt at 18. Master Smith has coached "
            "multiple national champions and represented the United States in international "
            "competitions. He specializes in ne-waza (ground techniques) and competition "
            "strategy. Currently teaching at Pacific Judo Academy in San Francisco, "
            "he offers group classes for all ages and private lessons for serious competitors."
        ),
        "embedding": SAMPLE_EMBEDDINGS["profile_judo_master"],
        "metadata": {
            "location": "San Francisco, CA",
            "disciplines": ["judo"],
            "rank": "5th_dan",
            "experience_years": 30,
            "specialties": ["competition", "ne-waza", "coaching"],
            "school": "Pacific Judo Academy"
        },
        "tags": ["instructor", "judo", "5th-dan", "coaching", "competition", "san-francisco"],
        "visibility": "public",
        "search_weight": 1.2,
        "is_active": True
    },
    {
        "id": str(uuid4()),
        "source_type": "article",
        "source_id": str(uuid4()),
        "url": "https://wwmaa.com/articles/karate-belt-system",
        "title": "Understanding the Karate Belt Ranking System",
        "content_chunk": (
            "The colored belt system in karate was popularized by Gichin Funakoshi, "
            "the founder of Shotokan karate. Students progress through white, yellow, "
            "orange, green, blue, and brown belts before reaching black belt (shodan). "
            "Each belt represents not just technical proficiency but also character "
            "development and understanding of karate philosophy. The journey to black "
            "belt typically takes 3-5 years of dedicated practice. Beyond first degree "
            "black belt, practitioners can advance to higher dans, with 10th dan being "
            "the highest rank, usually awarded posthumously or to legendary masters."
        ),
        "embedding": SAMPLE_EMBEDDINGS["article_belt_ranking"],
        "metadata": {
            "category": "education",
            "publish_date": "2024-09-20",
            "author": "Sensei Michael Brown",
            "reading_time": "6 minutes",
            "difficulty": "beginner"
        },
        "tags": ["education", "karate", "belt-system", "ranking", "beginner-guide"],
        "visibility": "public",
        "search_weight": 1.3,
        "is_active": True
    },
    {
        "id": str(uuid4()),
        "source_type": "video",
        "source_id": str(uuid4()),
        "url": "https://wwmaa.com/videos/kata-tutorial-heian-shodan",
        "title": "Heian Shodan Kata Tutorial - Step by Step Breakdown",
        "content_chunk": (
            "This comprehensive video tutorial breaks down Heian Shodan, the first kata "
            "in the Heian series and often the first kata taught to karate students. "
            "Master instructor demonstrates each movement with detailed explanations of "
            "stances (dachi), blocks (uke), and strikes (tsuki). Learn the proper rhythm, "
            "breathing, and application (bunkai) of each technique. Perfect for white and "
            "yellow belt students preparing for their first kata examination. Duration: "
            "25 minutes. Includes slow-motion replay and multiple camera angles."
        ),
        "embedding": SAMPLE_EMBEDDINGS["video_kata_tutorial"],
        "metadata": {
            "duration_seconds": 1500,
            "skill_level": "beginner",
            "disciplines": ["karate"],
            "video_type": "tutorial",
            "kata_name": "Heian Shodan",
            "views": 5420
        },
        "tags": ["video", "kata", "tutorial", "karate", "heian-shodan", "beginner"],
        "visibility": "public",
        "search_weight": 1.4,
        "is_active": True
    }
]


# ============================================================================
# QUERY SAMPLES FOR TESTING
# ============================================================================

SAMPLE_QUERIES = [
    {
        "query": "karate tournaments in Los Angeles",
        "embedding": SAMPLE_EMBEDDINGS["query_tournament_near_me"],
        "expected_source_types": ["event"],
        "expected_tags": ["tournament", "karate", "los-angeles"]
    },
    {
        "query": "beginner martial arts classes",
        "embedding": SAMPLE_EMBEDDINGS["query_beginner_classes"],
        "expected_source_types": ["event", "article", "video"],
        "expected_tags": ["beginner"]
    },
    {
        "query": "black belt requirements and ranking",
        "embedding": SAMPLE_EMBEDDINGS["query_black_belt_requirements"],
        "expected_source_types": ["article"],
        "expected_tags": ["belt-system", "ranking", "education"]
    },
    {
        "query": "history of Korean martial arts",
        "embedding": SAMPLE_EMBEDDINGS["query_martial_arts_history"],
        "expected_source_types": ["article"],
        "expected_tags": ["history", "taekwondo"]
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_embedding_by_name(name: str) -> List[float]:
    """Get a sample embedding by name"""
    return SAMPLE_EMBEDDINGS.get(name, generate_mock_embedding(999))


def get_content_by_type(source_type: str) -> List[Dict[str, Any]]:
    """Filter sample content by source type"""
    return [c for c in SAMPLE_CONTENT if c["source_type"] == source_type]


def get_all_embeddings() -> Dict[str, List[float]]:
    """Get all sample embeddings"""
    return SAMPLE_EMBEDDINGS.copy()


def get_all_content() -> List[Dict[str, Any]]:
    """Get all sample content"""
    return SAMPLE_CONTENT.copy()


def get_all_queries() -> List[Dict[str, Any]]:
    """Get all sample queries"""
    return SAMPLE_QUERIES.copy()
