from langgraph.prebuilt import create_react_agent
from models.llm import llm
from playwright.async_api import async_playwright
# Import từ file riêng (tool đã dùng @tool với args_schema)
from tools.brute_force_tool import bruteforce_with_wordlist_tool, get_playwright_tools
tools = [bruteforce_with_wordlist_tool]

# Hàm chính để gọi agent async
async def run_bruteforce_agent(target: str, plan: str = None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        tools.extend(get_playwright_tools(page, llm))
        agent_executor = create_react_agent(llm, tools)
        content = f"Target: {target}"
        if plan:
            content += f"\nPlan: {plan}"
        result= await agent_executor.ainvoke({
            "messages": [
                {"role": "user", "content": content}
            ]
        })
        await browser.close()
        if isinstance(result, dict):
            return result.get("output", str(result))
        return str(result)