from langgraph.prebuilt import create_react_agent
from models.llm import llm
from tools.password_guess_tool import RunSQLMap, RunNoSQLMap, RunHydra
agent_executor = None

async def run_password_guess_agent(target, plan=None):
    global agent_executor

    tools = [RunSQLMap, RunNoSQLMap, RunHydra]
    agent_executor = create_react_agent(llm, tools)

    content = f"Target: {target}"
    if plan:
        content += f"\nPlan: {plan}"

    result = await agent_executor.ainvoke({
        "messages": [{"role": "user", "content": content}]
    })

    if isinstance(result, dict):
        return result.get("output", str(result))
    return str(result)
