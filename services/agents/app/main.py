"""ZYNTRA Agents API — auth via API keys, ownership-safe CRUD, gateway-backed runs."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Agent, AgentRun, ApiKey, User, Workflow, get_session, init_db
from app.gateway_client import chat
from app.security import generate_api_key, hash_api_key


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = FastAPI(title="ZYNTRA Agents", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):  # type: ignore[no-untyped-def]
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


class RegisterIn(BaseModel):
    email: EmailStr


class RegisterOut(BaseModel):
    user_id: int
    email: str
    api_key: str = Field(description="Shown once — store securely")
    key_prefix: str


class AgentIn(BaseModel):
    name: str
    system_prompt: str = "You are a helpful agent."
    model: str = "gpt-4o-mini"


class AgentOut(BaseModel):
    id: int
    name: str
    system_prompt: str
    model: str


class RunIn(BaseModel):
    input_text: str


class RunOut(BaseModel):
    id: int
    status: str
    output_text: str | None


class WorkflowIn(BaseModel):
    name: str
    definition_json: str = "{}"


async def current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    raw = authorization.split(" ", 1)[1].strip()
    digest = hash_api_key(raw)
    result = await session.execute(select(ApiKey).where(ApiKey.key_hash == digest))
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    user = await session.get(User, key.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "zyntra-agents"}


@app.post("/v1/register", response_model=RegisterOut)
async def register(
    body: RegisterIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RegisterOut:
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=body.email)
    session.add(user)
    await session.flush()

    raw, digest, prefix = generate_api_key()
    session.add(ApiKey(user_id=user.id, key_hash=digest, key_prefix=prefix, name="default"))
    await session.commit()

    return RegisterOut(user_id=user.id, email=user.email, api_key=raw, key_prefix=prefix)


@app.post("/v1/agents", response_model=AgentOut)
async def create_agent(
    body: AgentIn,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentOut:
    agent = Agent(
        user_id=user.id,
        name=body.name,
        system_prompt=body.system_prompt,
        model=body.model,
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return AgentOut(
        id=agent.id,
        name=agent.name,
        system_prompt=agent.system_prompt,
        model=agent.model,
    )


@app.get("/v1/agents", response_model=list[AgentOut])
async def list_agents(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AgentOut]:
    result = await session.execute(select(Agent).where(Agent.user_id == user.id))
    agents = result.scalars().all()
    return [
        AgentOut(id=a.id, name=a.name, system_prompt=a.system_prompt, model=a.model)
        for a in agents
    ]


@app.get("/v1/agents/{agent_id}", response_model=AgentOut)
async def get_agent(
    agent_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentOut:
    agent = await session.get(Agent, agent_id)
    if agent is None or agent.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut(
        id=agent.id,
        name=agent.name,
        system_prompt=agent.system_prompt,
        model=agent.model,
    )


@app.delete("/v1/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    agent = await session.get(Agent, agent_id)
    if agent is None or agent.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    await session.delete(agent)
    await session.commit()


@app.post("/v1/agents/{agent_id}/runs", response_model=RunOut)
async def run_agent(
    agent_id: int,
    body: RunIn,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunOut:
    agent = await session.get(Agent, agent_id)
    if agent is None or agent.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    messages = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": body.input_text},
    ]
    try:
        output = await chat(messages, model=agent.model)
        status_s = "completed"
    except Exception as exc:  # noqa: BLE001 — surface as failed run
        output = f"Error: {exc}"
        status_s = "failed"

    run = AgentRun(
        agent_id=agent.id,
        user_id=user.id,
        input_text=body.input_text,
        output_text=output,
        status=status_s,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return RunOut(id=run.id, status=run.status, output_text=run.output_text)


@app.get("/v1/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunOut:
    run = await session.get(AgentRun, run_id)
    if run is None or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunOut(id=run.id, status=run.status, output_text=run.output_text)


@app.post("/v1/workflows")
async def create_workflow(
    body: WorkflowIn,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    wf = Workflow(user_id=user.id, name=body.name, definition_json=body.definition_json)
    session.add(wf)
    await session.commit()
    await session.refresh(wf)
    return {"id": wf.id, "name": wf.name}


@app.get("/v1/workflows")
async def list_workflows(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, Any]]:
    result = await session.execute(select(Workflow).where(Workflow.user_id == user.id))
    return [{"id": w.id, "name": w.name} for w in result.scalars().all()]
