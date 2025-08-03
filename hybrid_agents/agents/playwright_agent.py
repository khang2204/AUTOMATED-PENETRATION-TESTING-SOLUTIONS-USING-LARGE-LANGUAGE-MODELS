from langgraph.prebuilt import create_react_agent
from models.llm import llm
from tools.playwright_tool import get_playwright_tools
from playwright.async_api import async_playwright
agent_executor = None

async def run_playwright_agent(target, plan=None):
    global agent_executor

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        tools = get_playwright_tools(page, llm)
        agent_executor = create_react_agent(llm, tools)

        content = f"Target: {target}"
        if plan:
            content += f"\nPlan: {plan}"

        result = await agent_executor.ainvoke(
            {
                "messages": [{"role": "user", "content": content}]
            },
            config={"recursion_limit": 100}
        )

        await browser.close()

        if isinstance(result, dict):
            return result.get("output", str(result))
        return str(result)
