"""
Knowledge Agent - Handles knowledge base searches and FAQ responses
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from agentic.tools.knowledge_tools import search_knowledge_base, get_article_by_id


KNOWLEDGE_AGENT_PROMPT = """You are a Knowledge Base Specialist for CultPass, a cultural experience subscription service.

Your role is to:
1. Search the knowledge base for relevant articles when users have questions
2. Provide accurate information based on official documentation
3. Use the suggested phrasing from articles when available
4. Be clear about what is and isn't covered in the knowledge base

Guidelines:
- Always search the knowledge base first before answering questions
- Quote relevant sections from articles when helpful
- If no relevant articles are found, say so clearly
- Be friendly and professional in your responses

Remember: You're helping users understand how CultPass works, not handling their specific account issues.
"""


def create_knowledge_agent(model: str = "gpt-4o-mini"):
    """Create a knowledge base agent"""
    llm = ChatOpenAI(model=model, temperature=0)

    agent = create_react_agent(
        name="knowledge_agent",
        model=llm,
        tools=[search_knowledge_base, get_article_by_id],
        prompt=SystemMessage(content=KNOWLEDGE_AGENT_PROMPT)
    )

    return agent
