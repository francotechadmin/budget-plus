# elasticsearch_simple_client/searcher.py

from elasticsearch import Elasticsearch
from .config import Config
from .search_query_builder import SearchQueryBuilder

class Searcher:
    def __init__(self, es_url: str = None):
        self._config = Config.default()
        self._builder = SearchQueryBuilder()
        es_url = self._config.es_url if es_url is None else es_url
        self._es_connecter = Elasticsearch([es_url], timeout=60)

    def ping(self):
        try:
            return self._es_connecter.ping()
        except Exception as e:
            print(f"Error pinging Elasticsearch: {e}")
            return False    

    def execute_search(self, field: str,
                       musts: list = None,
                       shoulds: list = None,
                       query_return_length: int = None,
                       index: str = None,
                       user_id: str = None):
        """
        Executes a search query against the Elasticsearch index.
        If a user_id is provided, adds a filter to return documents where either:
         - the document's user_id equals the provided user_id, OR
         - the document is a default entry (default: True).
        """
        if index is None:
            index = self._config.es_index
        if query_return_length is None:
            query_return_length = self._config.query_return_length

        # Build a filter clause: user-specific OR default entries.
        filters = []
        if user_id:
            filters.append({
                "bool": {
                    "should": [
                        {"match": {"user_id": user_id}},
                        {"match": {"default": True}}
                    ]
                }
            })

        query = self._builder.build_search_query(field=field,
                                                 musts=musts,
                                                 shoulds=shoulds,
                                                 filters=filters,
                                                 query_return_length=query_return_length)
        es_result = self._es_connecter.search(body=query, index=index)
        return es_result
