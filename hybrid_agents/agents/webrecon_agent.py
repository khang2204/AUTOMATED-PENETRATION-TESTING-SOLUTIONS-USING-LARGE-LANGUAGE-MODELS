from langgraph.prebuilt import create_react_agent
from models.llm import llm
# Import các hàm tool bạn muốn cho agent sử dụng (chọn bất kỳ!)
from tools.web_recon_tool import (
    whois_tool,
    dnsx_tool,
    whatweb_tool,
    sslscan_tool,
    nuclei_tool,
    dirsearch_tool,
    http_fetch_tool
)

# Chỉ cần chọn các tool bạn muốn expose cho agent (có thể thêm/bớt tùy ý)
tools = [
    whois_tool,
    dnsx_tool,
    whatweb_tool,
    sslscan_tool,
    nuclei_tool,
    dirsearch_tool,
    http_fetch_tool
]

agent_executor = create_react_agent(llm, tools)

def run_webrecon_agent(target, plan):
    print(f"[DEBUG] WebReconAgent target: {target}")
    print(f"[DEBUG] Plan: {plan}")
    try:
        result = agent_executor.invoke({
            "messages": [
                {"role": "user", "content": f"Target: {target}\nPlan: {plan}"}
            ]
        })
        print("[DEBUG] Agent executor result:", result)
        return result
    except Exception as e:
        print(f"[ERROR] WebReconAgent failed: {e}")
        return f"Agent execution failed: {e}"