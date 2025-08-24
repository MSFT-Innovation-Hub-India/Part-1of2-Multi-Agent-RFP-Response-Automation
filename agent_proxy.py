
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union
import requests
from autogen.agentchat.agent import Agent
from autogen.agentchat.assistant_agent import ConversableAgent
from autogen.runtime_logging import log_new_agent, logging_enabled

logger = logging.getLogger(__name__)


class AgentProxy(ConversableAgent):
    
    DEFAULT_MODEL_NAME = "gpt4-o"

    def __init__(
        self,
        name="Agent Proxy Assistant",
        instructions: Optional[str] = None,
        llm_config: Optional[Union[Dict, bool]] = None,
        **kwargs,
    ):

        self._verbose = kwargs.pop("verbose", False)

        super().__init__(
            name=name, system_message=instructions, human_input_mode="NEVER", llm_config=llm_config, **kwargs
        )
        if logging_enabled():
            log_new_agent(self, locals())

        self._unread_index = defaultdict(int)
        self.register_reply([Agent, None], AgentProxy._invoke_assistant, position=2)


    def _invoke_assistant(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        """
        Invokes the external Agent to generate a reply based on the given messages.

        Args:
            messages: A list of messages in the conversation history with the sender.
            sender: The agent instance that sent the message.
            config: Optional configuration for message processing.

        Returns:
            A tuple containing a boolean indicating success and the external agent's reply.
        """

        if messages is None:
            messages = self._oai_messages[sender]
        unread_index = self._unread_index[sender] or 0
        pending_messages = messages[unread_index:]

        print("calling external proxy agent for Collateral from Marketing & Communications ....")
        run_response_message = ''
        reply_content = ''
        # Process each unread message
        for message in pending_messages:
            if message["content"].strip() == "":
                continue

            input_message = {"query": message["content"]}
            headers = {'Content-Type': 'application/json'}

            # Forward the activity to the external bot service
            # run_response_message = requests.post("http://127.0.0.1:36919/api/autogen", json=input_message,headers=headers, timeout=100)
            run_response_message = requests.post("http://192.168.0.136:36919/api/autogen", json=input_message,headers=headers, timeout=100)
            # print(f"External bot response: {run_response_message.json()}, \n status code: {run_response_message.status_code}")

            if run_response_message.status_code == 200:
                # print('Final Response:', run_response_message.json())
                reply_content = run_response_message.json()['response']
            else:
                # reply_content = 'Error communicating with the external service'
                # error_message = f"Forwarding content: {run_response_message.status_code}, Response: {run_response_message.text}"
                # config.logging.error(error_message)
                print('some error happenned ... ')
        
        # assert len(run_response_message) > 0, "No response from the assistant."

        response = {
            "role": "assistant",
            "content": "",
        }

        response["content"] += reply_content
        # print(f"External bot response: {response}")

        self._unread_index[sender] = len(self._oai_messages[sender]) + 1
        return True, response