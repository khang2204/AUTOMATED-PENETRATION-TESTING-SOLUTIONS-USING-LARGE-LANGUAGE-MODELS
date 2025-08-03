from langgraph.prebuilt import create_react_agent
from models.llm import llm
from tools.ssrf_tool import get_ssrf_tools

tools = get_ssrf_tools()
agent_executor = create_react_agent(llm, tools)

async def run_ssrf_agent(target, plan=None):
    content = f"Target: {target}"
    if plan:
        content += f"\nPlan: {plan}"

    result = await agent_executor.ainvoke(
        {
            "messages": [{"role": "user", "content": content}]
        },
        config={"recursion_limit": 100}
    )

    if isinstance(result, dict):
        return result.get("output", str(result))
    return str(result)