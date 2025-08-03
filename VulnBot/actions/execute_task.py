import re
import time
from typing import List

from click import prompt
from pydantic import BaseModel
import json
from actions.run_code import RunCode
from actions.shell_manager import ShellManager
from config.config import Configs, Mode

from utils.log_common import build_logger
from prompt_toolkit import prompt
from actions.agent_api import call_agent_api
logger = build_logger()


class ExecuteResult(BaseModel):
    context: object
    response: str


class ExecuteTask(BaseModel):
    action: str
    instruction: str
    code: List[str]

    def parse_response(self) -> list[str]:
        print(f"[DEBUG] Parsing instruction: {self.instruction}")
        initial_matches = re.findall(
            r'<execute>\s*(.*?)\s*</execute>', self.instruction, re.DOTALL
        )

        cleaned_matches = []
        for match in initial_matches:

            if '<execute>' in match:
                inner_match = re.search(r'<execute>\s*(.*?)$', match)
                if inner_match:
                    cleaned_matches.append(inner_match.group(1).strip())
            else:
                cleaned_matches.append(match.strip())

        return cleaned_matches

    def run(self) -> ExecuteResult:
        if Configs.basic_config.mode == Mode.SemiAuto:
            if self.action == "Shell":
                result = self.shell_operation()
                # result = RunCode(timeout=300, commands=thought).execute_cmd()
                # if result == "":
                #     result = prompt("Since the command takes too long to run, "
                #                         "please enter the manual run command and enter the result.\n> ")
            else:
                result = prompt("Please enter the manual run command and enter the result.\n> ")
        elif Configs.basic_config.mode == Mode.Manual:
            result = prompt("Please enter the manual run command and enter the result.\n> ")
        else:
            result = self.shell_operation()

        return ExecuteResult(context={
            "action": self.action,
            "instruction": self.instruction,
            "code": self.code,
        }, response=result)

    def shell_operation(self):
        result = ""
        thought = self.parse_response() 
        self.code = thought
        logger.info(f"Running {thought}")
        # shell = ShellManager.get_instance().get_shell()
        
        # SMB_PROMPTS = [
        #     'command not found',
        #     '?Invalid command.'
        # ]
        # PASSWORD_PROMPTS = [
        #     'password:',
        #     'Password for',
        #     '[sudo] password for',
        # ]
        
        skip_next = False
        
        try:
            for i, cmd_obj in enumerate(self.code):
                if skip_next:
                    skip_next = False
                    continue
                
                if isinstance(cmd_obj, str):
                    try:
                        cmd_obj = json.loads(cmd_obj)
                    except json.JSONDecodeError as e:
                        return f"Invalid JSON string in command list: {cmd_obj}\nError: {e}"

                # cmd_obj là dict có keys agent_name, target, plan (optional)
                agent_name = cmd_obj.get("agent_name")
                target = cmd_obj.get("target")
                plan = cmd_obj.get("plan", None)
                
                if not agent_name or not target:
                    return f"Invalid command object missing agent_name or target: {cmd_obj}"
                
                result += f'Action:<execute> agent_name={agent_name} target={target} </execute>\nObservation: '
                
                if plan:
                    output = call_agent_api(agent_name=agent_name, target=target, plan=plan)
                else:
                    output = call_agent_api(agent_name=agent_name, target=target)
                print(f"[SUCCESS] Command executed successfully. The output is:{output}")

                if not output:
                    output = "No output from command execution."
                else:
                    try:
                        output = json.dumps(output, indent=2)
                    except (TypeError, ValueError):
                        output = str(output)  # Fallback nếu không dump được

                result += output + '\n'
        except Exception as e:
            print(e)
            result = "Error executing command: " + str(e)
        return result
