import autogen
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from graphrag.query.cli import run_local_search, run_global_search
from typing import List, Dict, Union, Annotated
import logging
from utils.embedding import OpenAIEmbedding

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM configuration
local_llm_config = {
    "config_list": [
        {
            "model": "ollama_chat/llama3.1:70b",
            "api_key": "ollama",
            "base_url": "http://0.0.0.0:8001"
        }
    ],
    "cache_seed": None,
    "timeout": 60000
}


def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" in x.get("content", "")


class GraphRAGRetrieverAgent(RetrieveUserProxyAgent):
    def __init__(self, name, graphrag_config, **kwargs):
        retrieve_config = kwargs.get('retrieve_config', {})
        kwargs['retrieve_config'] = retrieve_config
        super().__init__(name=name, **kwargs)
        self.graphrag_config = graphrag_config

    def query_vector_db(
            self,
            query_texts: List[str],
            n_results: int = 10,
            search_string: str = "",
            **kwargs,
    ) -> Dict[str, Union[List[str], List[List[str]]]]:
        logger.info(f"Running GraphRAG query for: {query_texts}")

        all_results = []
        all_ids = []
        all_metadatas = []

        for query in query_texts:
            try:
                if self.graphrag_config.get('LOCAL_SEARCH', True):
                    result = run_local_search(
                        self.graphrag_config.get('INPUT_DIR'),
                        '..',
                        self.graphrag_config.get('COMMUNITY'),
                        self.graphrag_config.get('RESPONSE_TYPE'),
                        query
                    )
                else:
                    result = run_global_search(
                        self.graphrag_config.get('INPUT_DIR'),
                        self.graphrag_config.get('ROOT_DIR', '.'),
                        self.graphrag_config.get('COMMUNITY'),
                        self.graphrag_config.get('RESPONSE_TYPE'),
                        query
                    )
                print(f"GraphRAG query result: {result}")
                all_results.append([result])
                all_ids.append(["graphrag_result"])
                all_metadatas.append([{"source": "GraphRAG"}])

            except Exception as e:
                logger.error(f"Error in GraphRAG query: {str(e)}")
                all_results.append([f"An error occurred: {str(e)}"])
                all_ids.append(["error"])
                all_metadatas.append([{}])

        return {
            "ids": all_ids,
            "documents": all_results,
            "metadatas": all_metadatas
        }

    def retrieve_docs(self, problem: str, n_results: int = 20, search_string: str = "", **kwargs):
        results = self.query_vector_db(
            query_texts=[problem],
            n_results=n_results,
            search_string=search_string,
            **kwargs,
        )

        self._results = results
        logger.info(f"Retrieved result for problem: {problem}")

    @property
    def results(self):
        return self._results


# Define agents
boss = autogen.UserProxyAgent(
    name="Boss",
    is_termination_msg=termination_msg,
    human_input_mode="TERMINATE",
    system_message="The boss who asks questions and gives tasks.",
    code_execution_config=False
)

boss_aid = GraphRAGRetrieverAgent(
    name="Boss_Assistant",
    is_termination_msg=termination_msg,
    system_message="Assistant who has extra content retrieval power for solving difficult problems, please retrieve "
                   "all context for the problem.",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "qa",
        "embedding_function": OpenAIEmbedding(api_key="ollama"),
        "model": "ollama_chat/llama3.1:70b",
    },
    code_execution_config=False,
    graphrag_config={
        'LOCAL_SEARCH': True,
        'INPUT_DIR': None,
        'ROOT_DIR': '..',
        'COMMUNITY': 0,
        'RESPONSE_TYPE': 'multiple-page report'
    },
    llm_config=local_llm_config
)

coder = autogen.AssistantAgent(
    name="Senior_Java_Engineer",
    is_termination_msg=termination_msg,
    system_message="You are a senior Java engineer specializing in Spring applications. Reply `TERMINATE` in the end "
                   "when everything is done.",
    llm_config=local_llm_config,
)

pm = autogen.AssistantAgent(
    name="Product_Manager",
    is_termination_msg=termination_msg,
    system_message="You are a product manager. Reply `TERMINATE` in the end when everything is done.",
    llm_config=local_llm_config,
)

reviewer = autogen.AssistantAgent(
    name="Code_Reviewer",
    is_termination_msg=termination_msg,
    system_message="You are a code reviewer specializing in Java Spring applications. Reply `TERMINATE` in the end "
                   "when everything is done.",
    llm_config=local_llm_config,
)


def retrieve_content(
        message: Annotated[
            str,
            "Refined message which keeps the original meaning and can be used to retrieve content for code generation "
            "and question answering.",
        ],
        n_results: Annotated[int, "number of results"] = 3,
) -> str:
    boss_aid.n_results = n_results
    update_context_case1, update_context_case2 = boss_aid._check_update_context(message)
    if (update_context_case1 or update_context_case2) and boss_aid.update_context:
        boss_aid.problem = message if not hasattr(boss_aid, "problem") else boss_aid.problem
        _, ret_msg = boss_aid._generate_retrieve_user_reply(message)
    else:
        _context = {"problem": message, "n_results": n_results}
        ret_msg = boss_aid.message_generator(boss_aid, None, _context)
    return ret_msg if ret_msg else message


for caller in [pm, coder, reviewer]:
    d_retrieve_content = caller.register_for_llm(
        description="retrieve content for code generation and question answering.", api_style="function"
    )(retrieve_content)

for executor in [boss, pm]:
    executor.register_for_execution()(d_retrieve_content)

groupchat = autogen.GroupChat(
    agents=[boss, boss_aid, pm, coder, reviewer],
    messages=[],
    max_round=12,
    speaker_selection_method="round_robin",
    allow_repeat_speaker=False,
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=local_llm_config)

# Start chatting with the boss as this is the user proxy agent.
boss.initiate_chat(
    manager,
    message="Could you create a requirement table for the Digital team of MTV1898, including the integration of all "
            "applications? Please provide a step-by-step explanation of the tasks and a real-life scenario. Also, "
            "include how the workflow and integrations will appear from a technical perspective.",
)


