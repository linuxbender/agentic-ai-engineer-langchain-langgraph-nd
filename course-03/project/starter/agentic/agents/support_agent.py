"""
Main Support Agent - Primary customer-facing agent that orchestrates other agents
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from agentic.tools.knowledge_tools import search_knowledge_base
from agentic.tools.user_tools import get_user_info, get_user_subscription, get_user_reservations
from agentic.tools.experience_tools import get_available_experiences, get_experience_details
from agentic.tools.ticket_tools import get_ticket_info, update_ticket_status


SUPPORT_AGENT_PROMPT = """You are the CultPass Customer Support AI Assistant.

CultPass is a cultural experience subscription service that gives members access to museums, concerts, art exhibitions, and other cultural events in Brazil.

## Your Responsibilities:
1. **General Inquiries**: Answer questions about how CultPass works, subscriptions, and experiences
2. **Account Support**: Help users with account-related questions using their email to look up info
3. **Knowledge Base**: Search for relevant help articles to provide accurate information
4. **Experience Discovery**: Help users find and learn about available cultural experiences
5. **Issue Resolution**: Help resolve common issues and escalate when necessary

## Guidelines:
- Be friendly, professional, and empathetic
- Always search the knowledge base for relevant articles before answering policy questions
- When users ask about their account, ask for their email to look up their information
- For blocked accounts or complex issues, offer to escalate to human support
- Provide clear, actionable steps whenever possible
- Use the suggested phrasing from knowledge articles when available

## Subscription Tiers:
- **Basic**: 4 experiences per month, standard access
- **Premium**: 8 experiences per month, priority booking, exclusive events

## Common Issue Types:
- Login/access issues
- Subscription management (upgrade, downgrade, cancel, pause)
- Reservation questions (booking, canceling, availability)
- Payment and billing inquiries
- App technical issues

## Escalation Criteria:
- Payment refund requests
- Account security concerns
- Repeated technical issues
- User explicitly requests human support
- Blocked accounts due to policy violations

Remember: Always be helpful and look for ways to resolve the user's issue!
"""


def create_support_agent(model: str = "gpt-4o-mini"):
    """Create the main support agent with all tools"""
    llm = ChatOpenAI(model=model, temperature=0)

    all_tools = [
        # Knowledge tools
        search_knowledge_base,
        # User tools
        get_user_info,
        get_user_subscription,
        get_user_reservations,
        # Experience tools
        get_available_experiences,
        get_experience_details,
        # Ticket tools
        get_ticket_info,
        update_ticket_status,
    ]

    agent = create_react_agent(
        name="support_agent",
        model=llm,
        tools=all_tools,
        prompt=SystemMessage(content=SUPPORT_AGENT_PROMPT)
    )

    return agent
