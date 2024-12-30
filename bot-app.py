import autogen
from agent_proxy import AgentProxy
from flask import Flask, request, jsonify
import threading
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent

rfp_assistant_id = "asst_Cc0xciWLJxlnU11co3cAuP3H"
rfp_assistant_name = "ContosoEnggRfpAssistant"

rfp_assistant_config = {
    "tools": [
        {"type": "code_interpreter"},
    ],
    "tool_resources": {
        "code_interpreter": {
            "file_ids": ["assistant-OQhWYSEYHcHSmLuskzvrhzaQ"]
        }
    },
}

doc_writer_assistant_config = {
    "tools": [
        {"type": "code_interpreter"},
    ],
    "tool_resources": {
        "code_interpreter": {
            "file_ids": ["assistant-OQhWYSEYHcHSmLuskzvrhzaQ"]
        }
    },
}

user_proxy_system_prompt = """
You represent the Pre Sales Project Engineer tasked with helping compile a Response to an RFP shared in the input.
Once the RFP Response document is completed in all respects, you will save that to the working folder
Once the document is ready, you will conclude the conversation by typing 'TERMINATE'.
"""


group_chat_manager_system_prompt = """
You represent the Pre Sales Project Engineer tasked with helping compile a Response to an RFP shared in the input.
You will first ask for assistance from the ContosoEnggRfpAssistant to compile the RFP Response document.
Next reach out to CorpComms-Assistant-Proxy to get Customer testimonials and references.
You will ask the Document Writer to add the Customer testimonials information into the RFP Response document.
Once the Document Writer has compiled the document, let the User_proxy know that the work is complete and do not entertain any further messages.
"""
# # Configure logging
# logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# const.logging = logging
app = Flask(__name__)
# Define the URL of the external service
external_service_url = 'http://127.0.0.1:36919/api/autogen'

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4o"],
    },
)

rfp_assistant_system_prompt = "You are an AI Assistant that helps the Presales team at Contoso Engineering respond to RFPs from potential Customers. The user will refer to an RFP Document that is available with you and your task is to create an RFP Response document. Use your domain knowledge to fill in the details required in the Response. Ensure that the criteria stipulated by the Customer in the 'Proposal Requirements' section as honored.  Ensure that every section has a narration of atleast 250 characters. When the details in any section merit the use of tables to provide the content, do so. Leave the 'Customer Testimonials' and Customer References section alone blank in your response. Return the content of the document in Markdown format. Reply TERMINATE in the end when everything is done."

doc_writer_system_prompt = "Document Writer. Your job is to take the RFP Response prepared by ContosoEnggRfpAssistant, and add the Customer Testimonials prepared by CorpComms-Assistant-Proxy to it. Save the final content as a Microsoft Word Document .docx format in a shared folder."

# Define user proxy agent
llm_config = {"config_list": config_list_gpt4, "cache_seed": 45}
agent_proxy = AgentProxy(name="CorpComms-Assistant-Proxy", llm_config=llm_config, instructions=rfp_assistant_system_prompt)

doc_writer = GPTAssistantAgent(
    name="DocumentWriter",
    llm_config=llm_config,
    instructions=doc_writer_system_prompt,
assistant_config=doc_writer_assistant_config
)

rfp_assistant = GPTAssistantAgent(
    name=rfp_assistant_name,
    instructions=rfp_assistant_system_prompt,
    llm_config={
        "config_list": config_list_gpt4,
    },
    assistant_config=rfp_assistant_config,
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message=user_proxy_system_prompt,
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "groupchat",
        "use_docker": False,
    },
    is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
      # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    human_input_mode="NEVER"
)


def extract_content(response) -> str:
    # chat_history
    extracted_content = ''
    chat_history = response.chat_history
    for entry in chat_history:
        if entry.get('role') == 'user' and entry.get('name') == 'CorpComms-Assistant-Proxy':
            extracted_content = entry.get('content')
            break
    return extracted_content

@app.route('/api/autogen', methods=['POST'])
def handle_autogen_request():
    user_query = request.json.get('query')
    # print(f"Received query: {user_query}")
    # Config.logging.info(f"Received query: {user_query}")
    groupchat = autogen.GroupChat(agents=[user_proxy,rfp_assistant, agent_proxy,doc_writer], messages=[], max_round=5, speaker_selection_method="auto")
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config,system_message=group_chat_manager_system_prompt)
    response = user_proxy.initiate_chat(manager, message=user_query)
    # print(f"*******  Response **********: {response}")
    # You can process the response here and return it
    return jsonify({"response": extract_content(response)})


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app
        self.port = None

    def run(self):
        self.port = 36920  # Example port
        app.logger.info(f"Service running on: http://127.0.0.1:{self.port}")
        self.app.run(port=self.port)

if __name__ == "__main__":
    server_thread = ServerThread(app)
    server_thread.start()
    try:
        server_thread.join()
    except (KeyboardInterrupt, SystemExit):
        app.logger.info("Shutting down server...")
        # Add any cleanup code here