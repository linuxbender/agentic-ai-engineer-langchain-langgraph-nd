"""
Account Agent - Handles user account inquiries and subscription management
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from agentic.tools.user_tools import get_user_info, get_user_subscription, get_user_reservations
from agentic.tools.experience_tools import get_available_experiences, get_experience_details


ACCOUNT_AGENT_PROMPT = """You are an Account Specialist for CultPass, a cultural experience subscription service.

Your role is to:
1. Look up user account information when needed
2. Check subscription status and tier details
3. View and explain user reservations
4. Help users find available experiences
5. Explain account-related issues clearly

Guidelines:
- Always verify user email before sharing account details
- Be clear about subscription tiers (Basic vs Premium)
- Explain what actions the user can take in the app
- If a user's account is blocked, be empathetic and explain next steps
- Never share sensitive information without proper verification

When checking accounts:
1. First get user info by email
2. Then check subscription if needed
3. Look up reservations if the query is about bookings

For experience inquiries:
- Show available experiences that match user's preferences
- Note if an experience is premium and user's tier
- Mention slots available and dates
"""


def create_account_agent(model: str = "gpt-4o-mini"):
    """Create an account management agent"""
    llm = ChatOpenAI(model=model, temperature=0)

    agent = create_react_agent(
        name="account_agent",
        model=llm,
        tools=[
            get_user_info,
            get_user_subscription,
            get_user_reservations,
            get_available_experiences,
            get_experience_details
        ],
        prompt=SystemMessage(content=ACCOUNT_AGENT_PROMPT)
    )

    return agent
