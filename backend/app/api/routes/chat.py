import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.agents.base import BaseAgent
from app.core.agents.registry import agent_registry
from app.core.brain.startup_brain import startup_brain
from app.core.router.moe_router import moe_router
from app.core.router.types import RoutingPlan
from app.dependencies import get_db
from app.middleware.rate_limiter import CHAT_RATE_LIMIT, limiter
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.user import User
from app.models.venture import Venture
from app.models.workspace import WorkspaceMembership
from app.schemas.chat import (
    ChatMessageResponse,
    ChatSessionListResponse,
    ChatSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


async def _verify_workspace_and_get_venture(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Venture:
    """Verify workspace membership and return the venture."""
    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    venture_result = await db.execute(
        select(Venture).where(Venture.workspace_id == workspace_id)
    )
    venture = venture_result.scalar_one_or_none()
    if venture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace has no venture configured",
        )
    return venture


def _resolve_agent(routing_plan: RoutingPlan) -> BaseAgent:
    """Resolve the agent from routing plan, falling back to venture-architect."""
    agent = agent_registry.get(routing_plan.selected_agent)
    if agent is None:
        agent = agent_registry.get("venture-architect")
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No agents available",
        )
    return agent


async def _sse_event_stream(
    agent: BaseAgent,
    prompt: str,
    venture: Venture,
    routing_plan: RoutingPlan,
    session: ChatSession,
    user_id: str,
    db: AsyncSession,
) -> AsyncIterator[str]:
    """Generate SSE events: routing → token* → done."""
    # Event 1: routing metadata
    routing_data = routing_plan.model_dump()
    yield f"event: routing\ndata: {json.dumps(routing_data)}\n\n"

    # Events 2..N: token stream
    full_content: list[str] = []
    async for token in agent.execute_streaming(
        prompt=prompt,
        brain=startup_brain,
        db=db,
        venture=venture,
        routing_plan=routing_plan,
        session_id=str(session.id),
        user_id=user_id,
    ):
        full_content.append(token)
        yield f"event: token\ndata: {json.dumps(token)}\n\n"

    # Save complete assistant message
    complete_text = "".join(full_content)
    from app.core.agents.base import UPDATE_PATTERN

    citations = BaseAgent._extract_citations(complete_text)
    proposed_updates = BaseAgent._extract_proposed_updates(complete_text)
    clean_content = UPDATE_PATTERN.sub("", complete_text).strip()

    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=clean_content,
        agent_id=routing_plan.selected_agent,
        routing_plan=routing_plan.model_dump(),
        citations=citations,
    )
    db.add(assistant_msg)
    await db.flush()

    # Event N+1: done with metadata
    done_data: dict[str, Any] = {
        "message_id": str(assistant_msg.id),
        "citations": citations,
        "proposed_updates": proposed_updates,
        "artifact_id": None,
    }
    yield f"event: done\ndata: {json.dumps(done_data)}\n\n"


@router.post("/send", response_model=None)
@limiter.limit(CHAT_RATE_LIMIT)
async def send_message(
    request: Request,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse | StreamingResponse:
    """Send a message. Returns JSON or SSE stream based on Accept header."""
    workspace_id = uuid.UUID(body.workspace_id)
    venture = await _verify_workspace_and_get_venture(
        workspace_id, current_user.id, db
    )

    # Load or create session
    if body.session_id:
        session_uuid = uuid.UUID(body.session_id)
        session_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_uuid,
                ChatSession.workspace_id == workspace_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
    else:
        session = ChatSession(
            workspace_id=workspace_id,
            title=body.content[:100],
        )
        db.add(session)
        await db.flush()

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # Route the message
    routing_plan = moe_router.route(
        message=body.content,
        venture_stage=venture.stage,
        override_agent=body.override_agent,
    )

    agent = _resolve_agent(routing_plan)

    # Check Accept header for streaming
    accept = request.headers.get("accept", "application/json")
    if "text/event-stream" in accept:
        return StreamingResponse(
            _sse_event_stream(
                agent=agent,
                prompt=body.content,
                venture=venture,
                routing_plan=routing_plan,
                session=session,
                user_id=str(current_user.id),
                db=db,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming: existing JSON response
    response = await agent.execute(
        prompt=body.content,
        brain=startup_brain,
        db=db,
        venture=venture,
        routing_plan=routing_plan,
        session_id=str(session.id),
        user_id=str(current_user.id),
    )

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=response.content,
        agent_id=routing_plan.selected_agent,
        routing_plan=routing_plan.model_dump(),
        citations=response.citations,
    )
    db.add(assistant_msg)
    await db.flush()

    return SendMessageResponse(
        session_id=str(session.id),
        user_message=ChatMessageResponse(
            id=str(user_msg.id),
            role=user_msg.role,
            content=user_msg.content,
            agent_id=None,
            citations=None,
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessageResponse(
            id=str(assistant_msg.id),
            role=assistant_msg.role,
            content=assistant_msg.content,
            agent_id=assistant_msg.agent_id,
            citations=assistant_msg.citations,
            created_at=assistant_msg.created_at,
        ),
        routing_plan=routing_plan,
        proposed_updates=response.proposed_updates,
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionListResponse:
    """List chat sessions for a workspace."""
    ws_id = uuid.UUID(workspace_id)

    # Verify membership
    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == ws_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.workspace_id == ws_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = list(result.scalars().all())

    return ChatSessionListResponse(
        sessions=[
            ChatSessionResponse(
                id=str(s.id),
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Get a chat session with its messages."""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Verify workspace membership
    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == session.workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    return ChatSessionResponse(
        id=str(session.id),
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            ChatMessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                agent_id=m.agent_id,
                citations=m.citations,
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )
