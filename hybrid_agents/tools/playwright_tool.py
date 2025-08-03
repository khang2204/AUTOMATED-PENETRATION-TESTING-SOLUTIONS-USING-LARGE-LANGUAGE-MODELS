from langchain_core.tools import tool
from pydantic import BaseModel
from urllib.parse import urlparse, urlunparse, urlencode

class GoToWebsiteInput(BaseModel):
    url: str

class ClickElementInput(BaseModel):
    description: str

class WriteIntoElementInput(BaseModel):
    field: str
    text: str

class FindElementInput(BaseModel):
    description: str

class URLi(BaseModel):
    url: str
    payload: str

class RequestInput(BaseModel):
    request: str
    
class Dummy(BaseModel): pass

class PlaywrightToolsetAsync:
    def __init__(self, page, llm):
        self.page = page
        self.llm = llm
        self.page_html = None

    async def find_element(self, desc: str) -> str:
        self.page_html = await self.page.content()
        prompt = f"""
You are an automation agent. Your job is to find an XPath to an HTML element, using the full DOM structure below.

### Description:
The user wants to interact with an element described as:
"{desc}"

### DOM (truncated):
{self.page_html}

### Your task:
- Parse the DOM and understand the structure.
- Match the user's vague intent to an element that best fits semantically.
- Match on id, name, placeholder, aria-label, visible text, or associated <label for=...>.
- Avoid relying only on exact text matching.
- Use flexible XPath syntax with contains(...) to allow partial matches.
- The element doesn't have to match the description exactly, but it must exist in the HTML and be the most semantically relevant match.

### Output:
- Only output the XPath string.
- The XPath must work in Playwright with page.locator("xpath=...").
- No explanation, no code block, just the XPath.
"""
        xpath = (await self.llm.ainvoke(prompt)).content.strip()

        # Strip accidental triple-backtick wrapping or language labels
        if xpath.startswith("```"):
            xpath = xpath.strip("`").replace("xpath", "").strip()

        # Optional fallback if LLM fails completely
        if not xpath or len(xpath) < 4:
            return "//input"  # safe fallback
        print(f"Generated XPath for '{desc}': {xpath}")
        return xpath

    async def go_to_website(self, url: str) -> str:
        await self.page.goto(url)
        self.page_html = await self.page.content()
        return f"Visited {url}"

    async def click_element(self, desc: str) -> str:
        xpath = await self.find_element(desc)

        if xpath.startswith("```"):
            xpath = xpath.strip("`").replace("xpath", "").strip()

        if "no input elements" in xpath.lower():
            return f"❌ LLM could not find a clickable element for: {desc}"

        try:
            old_content = await self.page.content()
            await self.page.locator(f"xpath={xpath}").click()
            await self.page.wait_for_load_state("domcontentloaded")
            new_content = await self.page.content()

            # Gửi nguyên vẹn content cho LLM phân tích
            prompt = f"""
    You are an automated web security testing assistant.

    The user clicked on an element described as:
    "{desc}"

    Here is the full HTML content BEFORE clicking:
    ===
    {old_content}
    ===

    Here is the full HTML content AFTER clicking:
    ===
    {new_content}
    ===

    Your task is to determine whether the click action likely led to a successful outcome.

    Respond with:
    1. YES or NO
    2. A short explanation of your reasoning based on semantic or visual differences
    3. (Optional) Any specific words or content changes that helped you decide
    """
            llm_response = await self.llm.ainvoke(prompt)

            return (
                f"✅ Clicked on element matching: {desc}\n"
                f"📊 LLM Analysis Result:\n{llm_response.content.strip()}"
            )

        except Exception as e:
            return f"❌ Failed to click '{desc}' using XPath: {xpath}. Error: {str(e)}"

    async def write_into_element(self, field: str, text: str) -> str:
        xpath = await self.find_element(field)

        # Nếu nó trả về markdown block, strip nó đi
        if xpath.startswith("```"):
            xpath = xpath.strip("`").replace("xpath", "").strip()

        # Bỏ luôn trường hợp trả về lỗi
        if "no input elements" in xpath.lower():
            return f"❌ LLM could not find a matching input field for: {field}"

        try:
            await self.page.locator(f"xpath={xpath}").fill(text)
            return f"✅ Wrote '{text}' into '{field}' using XPath: {xpath}"
        except Exception as e:
            return f"❌ Failed to write into field '{field}' using XPath: {xpath}. Error: {str(e)}"
        await self.page.locator(xpath).fill(text)
        return f"Wrote '{text}' into '{field}'"

    async def FindParamInjection(self, base_url: str) -> list[str]:
        """
        Return the list of possible query parameters for the given URL based on LLM reasoning with page_content.
        """
        await self.page.goto(base_url)
        page_content = await self.page.content()

        prompt = f"""
You are given the HTML content of a web page at the URL: {base_url}

Here is the HTML content (truncated to 15000 chars):

{page_content}

Based on this content and common web practices, please list all possible query parameter names that could be used with this URL to filter, search, or input data. 
Only return a JSON list of strings, e.g.:

["q", "search", "id", "default", "page", "sort"]

Do not include any other text.
"""
        response = await self.llm.ainvoke(prompt)
        try:
            import json
            params = json.loads(response.content.strip())
            if not isinstance(params, list):
                params = []
        except Exception:
            params = []
        return params

    def generate_urls_with_payloads(self, base_url: str, params: list[str], payloads: list[str]) -> list[str]:
        """
        Sinh danh sách URL chèn payload vào từng param.
        """
        parsed = urlparse(base_url)
        injected_urls = []
        for param in params:
            for payload in payloads:
                query = urlencode({param: payload})
                new_url = urlunparse(parsed._replace(query=query))
                injected_urls.append(new_url)
        return injected_urls
    
    async def get_now_request(self):
        captured = {}

        def capture_request(req):
            captured.update({
                "method": req.method,
                "url": req.url,
                "headers": req.headers,
                "post_data": req.post_data
            })

        self.page.once("request", capture_request)

        # Gửi lại request đến chính URL hiện tại
        await self.page.goto(self.page.url)

        return captured or {"error": "No request captured"}

def get_playwright_tools(page, llm):
    toolset = PlaywrightToolsetAsync(page, llm)

    @tool(args_schema=GoToWebsiteInput)
    async def GoToWebsite(url: str) -> str:
        """Go to a specific URL."""
        return await toolset.go_to_website(url)

    @tool(args_schema=ClickElementInput)
    async def ClickElement(description: str) -> str:
        """Click an element by plain description (e.g. 'login button')."""
        return await toolset.click_element(description)

    @tool(args_schema=WriteIntoElementInput)
    async def WriteIntoElement(field: str, text: str) -> str:
        """
        Write into a form field based on its description.
        The description can be the natural language name of the field (e.g. 'username input', 'search box').
        The text is the value to write into the field.
        Example: write 'admin' into the field 'username input'.
        """
        return await toolset.write_into_element(field, text)

    @tool(args_schema=FindElementInput)
    async def FindElement(description: str) -> str:
        """Return XPath for given element description."""
        return await toolset.find_element(description)

    @tool(args_schema=URLi)
    async def InjectURLPayloads(url: str, payload: str) -> str:
        """
        Inject SQLi or XSS payloads into the given base URL.
        The tool uses LLM to infer possible query parameters, generates injected URLs,
        Sends requests, and returns status and response snippets.
        Example write the payload='<script>alert(1)</script>' to the URL 'https://example.com/search'.
        """
        params = await toolset.FindParamInjection(url)
        injected_urls = toolset.generate_urls_with_payloads(url, params, payload)

        return await toolset.go_to_website(injected_urls[0])

    @tool(args_schema=Dummy)
    async def GetNowRequest() -> str:
        """Reload current page and return the request just sent."""
        data = await toolset.get_now_request()
        import json
        return json.dumps(data, indent=2)
    
    @tool(args_schema=RequestInput)
    async def ModifyRequest(request: str) -> str:
        """
        Modify the request from GetNowRequest to exploit BAC or Authentication failure.
        Sends the modified request and returns response snippet.
        """
        # Step 1: Extract sensitive tokens
        prompt = f"""
            You are given a web request in JSON format:

            {request}

            Your task is modify this request to exploit a Broken Access Control or Authentication & Identification Failure vulnerability.
            Return only the request after modification in JSON format.
            Do not add any explanation or extra text.
        """
        response = await toolset.llm.ainvoke(prompt)
    
        # Step 3: Send the request
        try:
            import json
            req = json.loads(response.content.strip())
            url = req.get("url")
            method = req.get("method", "GET").upper()
            headers = req.get("headers", {})
            body = req.get("body", None)

            if not url:
                return "❌ Missing URL in modified request."

            if method == "GET":
                resp = await toolset.page.goto(url, wait_until="domcontentloaded")
                status = resp.status if resp else "unknown"
                content = await toolset.page.content()
            else:
                js = f"""
                    async () => {{
                        const res = await fetch("{url}", {{
                            method: "{method}",
                            headers: {json.dumps(headers)},
                            body: {json.dumps(body) if body else "null"}
                        }});
                        const text = await res.text();
                        return {{
                            status: res.status,
                            body: text.slice(0, 500)
                        }};
                    }}
                """
                result = await toolset.page.evaluate(js)
                status = result["status"]
                content = result["body"]

            return f"""✅ Modified request sent successfully.
    🔗 URL: {url}
    📬 Method: {method}
    📥 Status: {status}
    📄 Response Snippet:
    {content}"""
        
        except json.JSONDecodeError:
            return "❌ Cannot parse modified request as JSON."
        except Exception as e:
            return f"❌ Error sending request: {str(e)}"
    return [GoToWebsite, ClickElement, WriteIntoElement, FindElement, InjectURLPayloads, GetNowRequest, ModifyRequest]
