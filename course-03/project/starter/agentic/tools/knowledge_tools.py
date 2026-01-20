"""
Knowledge Base Tools for CultPass Support
"""
from typing import List, Dict, Any
from langchain_core.tools import tool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent paths
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
def search_knowledge_base(query: str, account_id: str = "cultpass") -> List[Dict[str, Any]]:
    """
    Search the knowledge base for articles relevant to a user query.
    Use this tool to find help articles, FAQs, and support documentation.

    Args:
        query: The search query or topic to find articles about
        account_id: The account ID (defaults to cultpass)

    Returns:
        List of matching knowledge articles with title, content, and tags
    """
    session = get_db_session()
    try:
        # Search for articles that match the query in title, content, or tags
        query_lower = query.lower()
        articles = session.query(udahub.Knowledge).filter(
            udahub.Knowledge.account_id == account_id
        ).all()

        results = []
        for article in articles:
            # Simple relevance scoring based on keyword matching
            score = 0
            title_lower = article.title.lower() if article.title else ""
            content_lower = article.content.lower() if article.content else ""
            tags_lower = article.tags.lower() if article.tags else ""

            # Check for query terms in title, content, and tags
            for term in query_lower.split():
                if term in title_lower:
                    score += 3
                if term in content_lower:
                    score += 1
                if term in tags_lower:
                    score += 2

            if score > 0:
                results.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "content": article.content,
                    "tags": article.tags,
                    "relevance_score": score
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:5]  # Return top 5 results

    finally:
        session.close()


@tool
def get_article_by_id(article_id: str) -> Dict[str, Any]:
    """
    Get a specific knowledge article by its ID.

    Args:
        article_id: The unique identifier of the article

    Returns:
        The knowledge article details or an error message
    """
    session = get_db_session()
    try:
        article = session.query(udahub.Knowledge).filter(
            udahub.Knowledge.article_id == article_id
        ).first()

        if article:
            return {
                "article_id": article.article_id,
                "title": article.title,
                "content": article.content,
                "tags": article.tags
            }
        else:
            return {"error": f"Article with ID {article_id} not found"}

    finally:
        session.close()
