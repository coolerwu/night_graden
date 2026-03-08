"""FastAPI Web 应用 / Web Application

提供 Web UI 和 API 接口：
- 页面路由（Jinja2 模板）
- API 路由（提交任务、SSE 流、workspace 管理、历史记录）
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from config.settings import WORKSPACE_ROOT
from graph.workflow import build_graph
from utils.workspace import WorkspaceManager
from utils.logger import get_logger
from web.sse import event_bus, sse_generator

logger = get_logger("web")

# --- App ---
app = FastAPI(title="Night Garden", docs_url="/docs")

# --- Static & Templates ---
_web_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=_web_dir / "static"), name="static")
templates = Jinja2Templates(directory=_web_dir / "templates")

# --- In-memory task store ---
tasks: dict[str, dict[str, Any]] = {}


# ─── Helpers ─────────────────────────────────────────────

def _get_workspace() -> WorkspaceManager:
    return WorkspaceManager(WORKSPACE_ROOT)


def _history_dir(ws: WorkspaceManager) -> Path:
    d = ws.root / ".history"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_history(ws: WorkspaceManager, task_id: str, data: dict):
    path = _history_dir(ws) / f"{task_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")


def _initial_state(requirement: str, workspace_root: str) -> dict:
    return {
        "messages": [],
        "workspace_root": workspace_root,
        "current_phase": "analyze",
        "task_description": requirement,
        "code_artifact": "",
        "code_file_path": "",
        "test_file_path": "",
        "test_result": "",
        "test_output": "",
        "deploy_status": "",
        "alert": "",
        "iteration": 0,
    }


# ─── Workflow Runner ─────────────────────────────────────

async def _run_workflow(task_id: str, requirement: str, workspace_root: str):
    """在后台线程中运行 LangGraph workflow，通过 SSE 推送进度"""
    graph = build_graph()
    state = _initial_state(requirement, workspace_root)

    tasks[task_id]["status"] = "running"

    loop = asyncio.get_event_loop()

    def _stream():
        """同步执行 graph.stream()（LangGraph 是同步的）"""
        results = {}
        for event in graph.stream(state):
            node_name = list(event.keys())[0]
            node_output = event[node_name]
            results[node_name] = node_output

            # 推送 SSE 事件
            sse_event = {
                "type": "agent_update",
                "agent": node_name,
                "phase": node_output.get("current_phase", ""),
                "data": _serialize_node_output(node_output),
            }
            loop.call_soon_threadsafe(
                asyncio.ensure_future,
                event_bus.publish(task_id, sse_event),
            )
        return results

    try:
        results = await loop.run_in_executor(None, _stream)
        tasks[task_id]["status"] = "done"
        tasks[task_id]["results"] = results

        # 保存历史
        ws = WorkspaceManager(workspace_root)
        _save_history(ws, task_id, {
            "task_id": task_id,
            "requirement": requirement,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": _serialize_node_output(results),
        })

    except Exception as e:
        logger.error("Workflow failed: %s", e)
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)
        await event_bus.publish(task_id, {
            "type": "error",
            "message": str(e),
        })

    await event_bus.publish(task_id, {"type": "done"})


def _serialize_node_output(obj: Any) -> Any:
    """确保输出可 JSON 序列化"""
    if isinstance(obj, dict):
        return {k: _serialize_node_output(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_node_output(i) for i in obj]
    if isinstance(obj, Path):
        return str(obj)
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


# ─── Page Routes ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request):
    ws = _get_workspace()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "workspace": ws,
    })


@app.get("/workspace", response_class=HTMLResponse)
async def page_workspace(request: Request):
    ws = _get_workspace()
    config = ws.get_config()

    # 列出 workspace 文件
    files = {}
    for subdir in ["src", "tests", "production"]:
        d = ws.root / ws.get_config().get(f"code_output_dir" if subdir == "src" else
                                           "test_output_dir" if subdir == "tests" else
                                           "deploy_dir", f"./{subdir}")
        if d.exists():
            files[subdir] = sorted([f.name for f in d.iterdir() if f.is_file()])
        else:
            files[subdir] = []

    return templates.TemplateResponse("workspace.html", {
        "request": request,
        "workspace": ws,
        "config": config,
        "files": files,
    })


@app.get("/history", response_class=HTMLResponse)
async def page_history(request: Request):
    ws = _get_workspace()
    history_path = _history_dir(ws)
    records = []
    for f in sorted(history_path.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            records.append(data)
        except Exception:
            pass
    return templates.TemplateResponse("history.html", {
        "request": request,
        "records": records[:50],
    })


# ─── API Routes ──────────────────────────────────────────

@app.post("/api/run")
async def api_run(request: Request):
    body = await request.json()
    requirement = body.get("requirement", "").strip()
    if not requirement:
        return JSONResponse({"error": "requirement is required"}, status_code=400)

    task_id = str(uuid.uuid4())[:8]
    ws = _get_workspace()

    tasks[task_id] = {
        "status": "pending",
        "requirement": requirement,
        "workspace_root": str(ws.root),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # 启动后台任务
    asyncio.create_task(_run_workflow(task_id, requirement, str(ws.root)))

    return JSONResponse({"task_id": task_id})


@app.get("/api/stream/{task_id}")
async def api_stream(task_id: str):
    if task_id not in tasks:
        return JSONResponse({"error": "task not found"}, status_code=404)
    return EventSourceResponse(sse_generator(task_id))


@app.get("/api/result/{task_id}")
async def api_result(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return JSONResponse({"error": "task not found"}, status_code=404)
    return JSONResponse(_serialize_node_output(task))


@app.get("/api/workspace")
async def api_workspace_get():
    ws = _get_workspace()
    return JSONResponse({
        "root": str(ws.root),
        "config": ws.get_config(),
    })


@app.put("/api/workspace")
async def api_workspace_update(request: Request):
    body = await request.json()
    ws = _get_workspace()
    import yaml
    config_path = ws.root / "workspace.yaml"
    current = ws.get_config()
    current.update(body)
    config_path.write_text(
        yaml.dump(current, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    return JSONResponse({"status": "updated", "config": current})


@app.get("/api/files/{file_path:path}")
async def api_file_read(file_path: str):
    ws = _get_workspace()
    full_path = ws.root / file_path
    if not full_path.exists() or not full_path.is_file():
        return JSONResponse({"error": "file not found"}, status_code=404)
    # 安全检查：确保在 workspace 内
    try:
        full_path.resolve().relative_to(ws.root.resolve())
    except ValueError:
        return JSONResponse({"error": "access denied"}, status_code=403)
    content = full_path.read_text(encoding="utf-8", errors="replace")
    return JSONResponse({"path": str(full_path), "content": content})


@app.get("/api/history")
async def api_history():
    ws = _get_workspace()
    history_path = _history_dir(ws)
    records = []
    for f in sorted(history_path.glob("*.json"), reverse=True):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return JSONResponse(records[:50])
