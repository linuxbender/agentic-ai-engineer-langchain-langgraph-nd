"""
Experience-related Tools for CultPass Support
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from data.models import cultpass


# Database connection
CULTPASS_DB = "data/external/cultpass.db"


def get_db_session():
    """Get a database session for cultpass"""
    engine = create_engine(f"sqlite:///{CULTPASS_DB}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


@tool
def get_available_experiences(
    location: Optional[str] = None,
    is_premium: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get available cultural experiences.
    Use this to help users find experiences they can book.

    Args:
        location: Optional filter by location
        is_premium: Optional filter for premium (True) or basic (False) experiences

    Returns:
        List of available experiences with details
    """
    session = get_db_session()
    try:
        query = session.query(cultpass.Experience)

        # Filter by future events only
        query = query.filter(cultpass.Experience.when >= datetime.now())

        # Apply optional filters
        if location:
            query = query.filter(
                cultpass.Experience.location.ilike(f"%{location}%")
            )

        if is_premium is not None:
            query = query.filter(cultpass.Experience.is_premium == is_premium)

        # Only show experiences with available slots
        query = query.filter(cultpass.Experience.slots_available > 0)

        experiences = query.order_by(cultpass.Experience.when).all()

        results = []
        for exp in experiences:
            results.append({
                "experience_id": exp.experience_id,
                "title": exp.title,
                "description": exp.description,
                "location": exp.location,
                "when": exp.when.isoformat() if exp.when else None,
                "slots_available": exp.slots_available,
                "is_premium": exp.is_premium
            })

        return results if results else [{"message": "No experiences found matching your criteria"}]

    finally:
        session.close()


@tool
def get_experience_details(experience_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific experience.

    Args:
        experience_id: The unique identifier of the experience

    Returns:
        Detailed experience information
    """
    session = get_db_session()
    try:
        experience = session.query(cultpass.Experience).filter(
            cultpass.Experience.experience_id == experience_id
        ).first()

        if experience:
            return {
                "experience_id": experience.experience_id,
                "title": experience.title,
                "description": experience.description,
                "location": experience.location,
                "when": experience.when.isoformat() if experience.when else None,
                "slots_available": experience.slots_available,
                "is_premium": experience.is_premium,
                "is_upcoming": experience.when >= datetime.now() if experience.when else False
            }
        else:
            return {"error": f"Experience with ID {experience_id} not found"}

    finally:
        session.close()
