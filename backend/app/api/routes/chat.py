"""Chat API routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.agents.router import get_agent_router
from app.core.brain.startup_brain import StartupBrain
from app.dependencies import get_db
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.user import User
from app.models.venture import Venture
from app.models.workspace import Workspace
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageListResponse,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
    CitationResponse,
    SendMessageResponse,
    StreamChunk,
    StreamChunkType,
)

router = APIRouter(prefix="/chat", tags=["chat"])


# --- Helper Functions ---


async def get_workspace_or_404(
    workspace_id: str,
    user: User,
    db: AsyncSession,
) -> Workspace:
    """Get workspace and verify access."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


async def get_session_or_404(
    session_id: str,
    user: User,
    db: AsyncSession,
) -> ChatSession:
    """Get chat session and verify access."""
    result = await db.execute(
        select(ChatSession)
        .join(Workspace)
        .where(
            ChatSession.id == session_id,
            Workspace.owner_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return session


def format_message_response(message: ChatMessage) -> ChatMessageResponse:
    """Format a ChatMessage model to response schema."""
    citations = []
    if message.citations:
        for c in message.citations:
            citations.append(
                CitationResponse(
                    chunk_id=c.get("chunk_id", ""),
                    document_id=c.get("document_id", ""),
                    snippet=c.get("snippet", ""),
                    score=c.get("score", 0.0),
                )
            )

    return ChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        agent_id=message.agent_id,
        citations=citations,
        routing_plan=message.routing_plan,
        created_at=message.created_at,
    )


# --- Session Endpoints ---


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    workspace_id: str,
    data: ChatSessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Create a new chat session in a workspace."""
    # Verify workspace access
    await get_workspace_or_404(workspace_id, user, db)

    session = ChatSession(
        id=str(uuid4()),
        workspace_id=workspace_id,
        title=data.title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionResponse(
        id=session.id,
        workspace_id=session.workspace_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    workspace_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionListResponse:
    """List chat sessions in a workspace."""
    await get_workspace_or_404(workspace_id, user, db)

    # Get sessions with message count
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.workspace_id == workspace_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.workspace_id == workspace_id)
    )
    total = count_result.scalar() or 0

    # Get message counts
    session_responses = []
    for session in sessions:
        msg_count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        msg_count = msg_count_result.scalar() or 0

        session_responses.append(
            ChatSessionResponse(
                id=session.id,
                workspace_id=session.workspace_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=msg_count,
            )
        )

    return ChatSessionListResponse(sessions=session_responses, total=total)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Get a chat session by ID."""
    session = await get_session_or_404(session_id, user, db)

    msg_count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
    )
    msg_count = msg_count_result.scalar() or 0

    return ChatSessionResponse(
        id=session.id,
        workspace_id=session.workspace_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=msg_count,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a chat session."""
    session = await get_session_or_404(session_id, user, db)
    await db.delete(session)
    await db.commit()


# --- Message Endpoints ---


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def list_messages(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageListResponse:
    """List messages in a chat session."""
    session = await get_session_or_404(session_id, user, db)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()

    count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
    )
    total = count_result.scalar() or 0

    return ChatMessageListResponse(
        messages=[format_message_response(m) for m in messages],
        total=total,
    )


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    data: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    """Send a message and get an AI response."""
    session = await get_session_or_404(session_id, user, db)

    # Get workspace to find venture
    result = await db.execute(select(Workspace).where(Workspace.id == session.workspace_id))
    workspace = result.scalar_one()

    # Find venture for this workspace (use first one)
    venture_result = await db.execute(
        select(Venture).where(Venture.workspace_id == workspace.id).limit(1)
    )
    venture = venture_result.scalar_one_or_none()

    # Create user message
    user_message = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.USER,
        content=data.content,
        user_id=user.id,
    )
    db.add(user_message)

    # Get chat history for context
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    history_messages = list(reversed(history_result.scalars().all()))

    history_context = [{"role": m.role.value, "content": m.content} for m in history_messages]

    # Initialize brain and router
    venture_id = venture.id if venture else workspace.id
    brain = StartupBrain(venture_id, db)
    agent_router = get_agent_router(brain)

    # Get AI response
    response = await agent_router.route(
        message=data.content,
        context={"history": history_context},
        agent_override=data.agent_override,
    )

    # Create assistant message
    assistant_message = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=response.content,
        agent_id=response.agent_id,
        routing_plan=response.routing_plan,
        citations=[c.model_dump() for c in response.citations] if response.citations else None,
    )
    db.add(assistant_message)

    # Update session timestamp
    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    return SendMessageResponse(
        user_message=format_message_response(user_message),
        assistant_message=format_message_response(assistant_message),
    )


@router.post("/sessions/{session_id}/stream")
async def stream_message(
    session_id: str,
    data: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a message response using Server-Sent Events."""
    session = await get_session_or_404(session_id, user, db)

    # Get workspace and venture
    result = await db.execute(select(Workspace).where(Workspace.id == session.workspace_id))
    workspace = result.scalar_one()

    venture_result = await db.execute(
        select(Venture).where(Venture.workspace_id == workspace.id).limit(1)
    )
    venture = venture_result.scalar_one_or_none()

    # Create user message
    user_message = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.USER,
        content=data.content,
        user_id=user.id,
    )
    db.add(user_message)
    await db.commit()

    # Get history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    history_messages = list(reversed(history_result.scalars().all()))
    history_context = [{"role": m.role.value, "content": m.content} for m in history_messages]

    # Initialize brain and router
    venture_id = venture.id if venture else workspace.id
    brain = StartupBrain(venture_id, db)
    agent_router = get_agent_router(brain)

    async def event_generator():
        """Generate SSE events."""
        full_content = []

        try:
            # First, send routing info
            agent_name = await agent_router.classify_intent(data.content)
            routing_chunk = StreamChunk(
                type=StreamChunkType.ROUTING,
                data={"agent": agent_name},
            )
            yield f"data: {routing_chunk.model_dump_json()}\n\n"

            # Stream content
            async for chunk in agent_router.route_stream(
                message=data.content,
                context={"history": history_context},
                agent_override=data.agent_override,
            ):
                full_content.append(chunk)
                content_chunk = StreamChunk(
                    type=StreamChunkType.CONTENT,
                    data=chunk,
                )
                yield f"data: {content_chunk.model_dump_json()}\n\n"

            # Save assistant message
            assistant_message = ChatMessage(
                id=str(uuid4()),
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content="".join(full_content),
                agent_id=agent_name,
            )
            db.add(assistant_message)
            session.updated_at = datetime.utcnow()
            await db.commit()

            # Send done event
            done_chunk = StreamChunk(
                type=StreamChunkType.DONE,
                data={"message_id": assistant_message.id},
            )
            yield f"data: {done_chunk.model_dump_json()}\n\n"

        except Exception as e:
            error_chunk = StreamChunk(
                type=StreamChunkType.ERROR,
                data={"error": str(e)},
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
