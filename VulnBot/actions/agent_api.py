import requests

def call_agent_api(agent_name: str, target: str, plan: dict) -> str:
    payload = {
        "agent_name": agent_name,
        "target": target,
        "plan": plan
    }
    try:
        print(f"Payload send to agent{payload}")
        response = requests.post(
            "http://192.168.229.128:8000/execute",
            json=payload,
            timeout=3000
        )
        response.raise_for_status()
        data = response.json()
        return data.get("result", "")
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except ValueError:
        return "Invalid JSON response from API"
