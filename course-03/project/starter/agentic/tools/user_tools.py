"""
User-related Tools for CultPass Support
"""
from typing import Dict, Any, List
from langchain_core.tools import tool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
def get_user_info(user_email: str) -> Dict[str, Any]:
    """
    Get user information by email address.
    Use this to look up customer details for support purposes.

    Args:
        user_email: The user's email address

    Returns:
        User information including ID, name, email, and account status
    """
    session = get_db_session()
    try:
        user = session.query(cultpass.User).filter(
            cultpass.User.email == user_email
        ).first()

        if user:
            return {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "is_blocked": user.is_blocked,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        else:
            return {"error": f"User with email {user_email} not found"}

    finally:
        session.close()


@tool
def get_user_subscription(user_id: str) -> Dict[str, Any]:
    """
    Get subscription details for a user.
    Use this to check subscription status, tier, and quota.

    Args:
        user_id: The user's unique identifier

    Returns:
        Subscription information including status, tier, and monthly quota
    """
    session = get_db_session()
    try:
        subscription = session.query(cultpass.Subscription).filter(
            cultpass.Subscription.user_id == user_id
        ).first()

        if subscription:
            return {
                "subscription_id": subscription.subscription_id,
                "user_id": subscription.user_id,
                "status": subscription.status,
                "tier": subscription.tier,
                "monthly_quota": subscription.monthly_quota,
                "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
                "ended_at": subscription.ended_at.isoformat() if subscription.ended_at else None
            }
        else:
            return {"error": f"No subscription found for user {user_id}"}

    finally:
        session.close()


@tool
def get_user_reservations(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all reservations for a user.
    Use this to check a user's upcoming or past bookings.

    Args:
        user_id: The user's unique identifier

    Returns:
        List of reservations with experience details and status
    """
    session = get_db_session()
    try:
        reservations = session.query(cultpass.Reservation).filter(
            cultpass.Reservation.user_id == user_id
        ).all()

        results = []
        for res in reservations:
            experience = session.query(cultpass.Experience).filter(
                cultpass.Experience.experience_id == res.experience_id
            ).first()

            results.append({
                "reservation_id": res.reservation_id,
                "experience_id": res.experience_id,
                "experience_title": experience.title if experience else "Unknown",
                "experience_location": experience.location if experience else "Unknown",
                "experience_when": experience.when.isoformat() if experience and experience.when else None,
                "status": res.status,
                "created_at": res.created_at.isoformat() if res.created_at else None
            })

        return results if results else [{"message": "No reservations found for this user"}]

    finally:
        session.close()
