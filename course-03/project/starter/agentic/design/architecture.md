# CultPass Customer Support - Multi-Agent Architecture

## Overview

This document describes the architecture of the CultPass Customer Support AI system, a multi-agent application built with LangGraph for handling customer inquiries about cultural experience subscriptions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                               │
│                   (Chat Interface)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                            │
│                  (Main Support Agent)                            │
│  - Routes queries to appropriate tools                           │
│  - Maintains conversation context                                │
│  - Uses MemorySaver for state persistence                        │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ KNOWLEDGE TOOLS │  │   USER TOOLS    │  │  TICKET TOOLS   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ search_knowledge│  │ get_user_info   │  │ get_ticket_info │
│ get_article_by_ │  │ get_user_sub    │  │ update_ticket_  │
│ id              │  │ get_user_res    │  │ add_ticket_msg  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   UDAHUB DB     │  │  CULTPASS DB    │  │   UDAHUB DB     │
│ (Knowledge Base)│  │ (User Accounts) │  │   (Tickets)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Components

### 1. Orchestrator Agent

The main entry point that handles all customer interactions. Built with `create_react_agent` from LangGraph.

**Responsibilities:**
- Understanding user intent
- Selecting appropriate tools
- Generating helpful responses
- Maintaining conversation state

**Configuration:**
- Model: GPT-4o-mini
- Temperature: 0 (deterministic responses)
- Checkpointer: MemorySaver for conversation persistence

### 2. Tools

#### Knowledge Tools (`knowledge_tools.py`)
- `search_knowledge_base`: Semantic search through help articles
- `get_article_by_id`: Retrieve specific article content

#### User Tools (`user_tools.py`)
- `get_user_info`: Look up customer by email
- `get_user_subscription`: Check subscription status/tier
- `get_user_reservations`: View customer bookings

#### Experience Tools (`experience_tools.py`)
- `get_available_experiences`: Browse upcoming events
- `get_experience_details`: Get specific event info

#### Ticket Tools (`ticket_tools.py`)
- `get_ticket_info`: View support ticket details
- `update_ticket_status`: Change ticket state
- `add_ticket_message`: Log conversation history

### 3. Databases

#### UdaHub Core DB (`udahub.db`)
- **Accounts**: Tenant information
- **Users**: Mapped external users
- **Tickets**: Support conversations
- **TicketMetadata**: Status, tags, issue types
- **TicketMessages**: Conversation history
- **Knowledge**: Help articles and FAQs

#### CultPass External DB (`cultpass.db`)
- **Users**: Customer accounts
- **Subscriptions**: Tier and quota info
- **Experiences**: Cultural events
- **Reservations**: Bookings

## Data Flow

1. User sends message via chat interface
2. Orchestrator receives message with thread_id
3. Agent analyzes intent and selects tools
4. Tools query appropriate databases
5. Agent generates response with tool results
6. Response returned to user
7. State persisted via MemorySaver

## Key Features

### State Management
- MemorySaver checkpointer maintains conversation context
- Thread-based isolation for multiple concurrent users
- Persistent state across sessions

### Tool Selection
- ReAct pattern for reasoning and acting
- Automatic tool selection based on query
- Fallback to knowledge base for unknown questions

### Error Handling
- Graceful degradation when tools fail
- Clear error messages for users
- Escalation path to human support

## Conversation Categories

1. **General Inquiries** → Knowledge Base Search
2. **Account Questions** → User Tools + Knowledge
3. **Booking Issues** → User Tools + Experience Tools
4. **Technical Problems** → Knowledge Base + Escalation
5. **Billing Questions** → Knowledge Base + Escalation

## Escalation Triggers

- Payment refund requests
- Blocked accounts
- Repeated failures
- Explicit human request
- Security concerns

## Future Enhancements

1. **Multi-Agent Architecture**: Specialized agents for different domains
2. **RAG Integration**: Vector-based semantic search
3. **Proactive Support**: Automated follow-ups
4. **Analytics**: Conversation insights and metrics
5. **Multi-language**: Portuguese support for Brazil market
