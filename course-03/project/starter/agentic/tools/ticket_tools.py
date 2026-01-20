"""
Ticket Management Tools for CultPass Support
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from data.models import udahub


# Database connection
UDAHUB_DB = "data/core/udahub.db"


def get_db_session():
    """Get a database session for udahub"""
    engine = create_engine(f"sqlite:///{UDAHUB_DB}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


@tool
def get_ticket_info(ticket_id: str) -> Dict[str, Any]:
    """
    Get information about a support ticket.
    Use this to understand the context of the current conversation.

    Args:
        ticket_id: The unique identifier of the ticket

    Returns:
        Ticket information including status, user, and message history
    """
    session = get_db_session()
    try:
        ticket = session.query(udahub.Ticket).filter(
            udahub.Ticket.ticket_id == ticket_id
        ).first()

        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found"}

        # Get ticket metadata
        metadata = session.query(udahub.TicketMetadata).filter(
            udahub.TicketMetadata.ticket_id == ticket_id
        ).first()

        # Get message history
        messages = session.query(udahub.TicketMessage).filter(
            udahub.TicketMessage.ticket_id == ticket_id
        ).order_by(udahub.TicketMessage.created_at).all()

        # Get user info
        user = session.query(udahub.User).filter(
            udahub.User.user_id == ticket.user_id
        ).first()

        return {
            "ticket_id": ticket.ticket_id,
            "channel": ticket.channel,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "user": {
                "user_id": user.user_id if user else None,
                "user_name": user.user_name if user else None,
                "external_user_id": user.external_user_id if user else None
            },
            "metadata": {
                "status": metadata.status if metadata else None,
                "main_issue_type": metadata.main_issue_type if metadata else None,
                "tags": metadata.tags if metadata else None
            },
            "messages": [
                {
                    "role": msg.role.value if msg.role else None,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        }

    finally:
        session.close()


@tool
def update_ticket_status(
    ticket_id: str,
    status: str,
    issue_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the status of a support ticket.
    Use this when resolving issues or escalating tickets.

    Args:
        ticket_id: The unique identifier of the ticket
        status: New status (open, in_progress, resolved, escalated)
        issue_type: Optional main issue type classification

    Returns:
        Updated ticket status confirmation
    """
    session = get_db_session()
    try:
        metadata = session.query(udahub.TicketMetadata).filter(
            udahub.TicketMetadata.ticket_id == ticket_id
        ).first()

        if not metadata:
            return {"error": f"Ticket metadata for {ticket_id} not found"}

        # Update status
        metadata.status = status
        if issue_type:
            metadata.main_issue_type = issue_type

        session.commit()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "new_status": status,
            "issue_type": issue_type or metadata.main_issue_type
        }

    except Exception as e:
        session.rollback()
        return {"error": f"Failed to update ticket: {str(e)}"}
    finally:
        session.close()


@tool
def add_ticket_message(
    ticket_id: str,
    content: str,
    role: str = "ai"
) -> Dict[str, Any]:
    """
    Add a message to a support ticket.
    Use this to log AI responses or important notes.

    Args:
        ticket_id: The unique identifier of the ticket
        content: The message content
        role: The role of the message sender (user, agent, ai, system)

    Returns:
        Confirmation of message addition
    """
    session = get_db_session()
    try:
        # Verify ticket exists
        ticket = session.query(udahub.Ticket).filter(
            udahub.Ticket.ticket_id == ticket_id
        ).first()

        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found"}

        # Create message
        message = udahub.TicketMessage(
            message_id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            role=role,
            content=content
        )

        session.add(message)
        session.commit()

        return {
            "success": True,
            "message_id": message.message_id,
            "ticket_id": ticket_id
        }

    except Exception as e:
        session.rollback()
        return {"error": f"Failed to add message: {str(e)}"}
    finally:
        session.close()
