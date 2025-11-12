
import logging
from typing import List, Dict, Union

import chainlit as cl
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from graphrag.query.cli import run_local_search, run_global_search

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                if self.graphrag_config.get('LOCAL_SEARCH', cl.user_session.get("LOCAL_SEARCH", True)):
                    result = run_local_search(
                        self.graphrag_config.get('INPUT_DIR'),
                        self.graphrag_config.get('ROOT_DIR', '.') if self.graphrag_config.get('ROOT_DIR') else '..',
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
