import inspect
from fastapi import APIRouter, Request

from agents.webrecon_agent import run_webrecon_agent
from agents.playwright_agent import run_playwright_agent
from agents.ssrf_agent import run_ssrf_agent
from agents.bruteforce_agent import run_bruteforce_agent
from agents.guess_pass_agent import run_password_guess_agent

agent_router = APIRouter()

@agent_router.post("/execute")
async def execute_agent(request: Request):
    data = await request.json()
    agent_name = data.get("agent_name")
    target = data.get("target")
    plan = data.get("plan", None)

    if not agent_name or not target:
        return {"error": "agent_name and target required"}

    agent_map = {
        "WebReconAgent": run_webrecon_agent,
        "PlaywrightAgent": run_playwright_agent,
        "SSRFAgent": run_ssrf_agent,
        "BruteForceAgent": run_bruteforce_agent,
        "PasswordGuessAgent": run_password_guess_agent,
    }

    agent_func = agent_map.get(agent_name)
    if not agent_func:
        return {"error": f"Unknown agent_name: {agent_name}"}

    try:
        if inspect.iscoroutinefunction(agent_func):
            if plan is not None:
                result = await agent_func(target, plan)
            else:
                result = await agent_func(target)
        else:
            if plan is not None:
                result = agent_func(target, plan)
            else:
                result = agent_func(target)
    except Exception as e:
        return {"error": str(e)}

    return {"result": result}
