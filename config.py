#filename : config.py
import chainlit as cl
from chainlit.input_widget import Select, Slider, Switch, TextInput
from tasks.task_initializer import initialize_tasks

local_llm_config = {
    "config_list": [
        {
            "model": "ollama_chat/llama3.1:70b",
            "api_key": "ollama",
            "base_url": "http://127.0.0.1:8001",
            "temperature": 0.8,
        }
    ],
    "cache_seed": None,
    "timeout": 60000
}


async def initialize_settings():
    task_list, processing_task, retriever_task, user_proxy_task, testing_agent_task, coding_agent_task, code_review_agent_task = await initialize_tasks()

    cl.user_session.set("task_list", task_list)
    cl.user_session.set("processing_task", processing_task)
    cl.user_session.set("retriever_task", retriever_task)
    cl.user_session.set("user_proxy_task", user_proxy_task)
    cl.user_session.set("testing_agent_task", testing_agent_task)
    cl.user_session.set("coding_agent_task", coding_agent_task)
    cl.user_session.set("code_review_agent_task", code_review_agent_task)

    settings = await cl.ChatSettings([
        Switch(id="Search_type", label="(GraphRAG) Local Search", initial=True),
        Select(id="Gen_type", label="(GraphRAG) Content Type",
               values=["prioritized list", "single paragraph", "multiple paragraphs", "multiple-page report"],
               initial_index=1),
        Select(id="Color_by", label="Color Nodes By", values=["community", "centrality", "degree"],
               initial_index=0),
        Select(id="Centrality_type", label="Centrality Type (if coloring by centrality)",
               values=["degree", "betweenness", "closeness"], initial_index=0),
        Slider(id="Community", label="(GraphRAG) Community Level", initial=0, min=0, max=2, step=1),
        Switch(id="Visualize_graph", label="Visualize Graph", initial=True),
        Select(id="Graph_layout", label="Graph Layout", values=["spring", "circular", "random"], initial_index=0),
        Slider(id="Node_size", label="Node Size Factor", initial=10, min=1, max=20, step=1),
        Slider(id="Edge_width", label="Edge Width", initial=0.5, min=0.1, max=2.0, step=0.1),
        TextInput(id="Highlight_nodes", label="Highlight Nodes (comma-separated)", initial="")
    ]).send()

    for key, value in settings.items():
        cl.user_session.set(key, value)
