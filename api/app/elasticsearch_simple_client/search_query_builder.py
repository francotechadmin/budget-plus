# elasticsearch_simple_client/search_query_builder.py

import json

class SearchQueryBuilder:
    """
    Query builder for searching a single index in Elasticsearch.
    Supports must, should and filter clauses.
    """

    @staticmethod
    def _match(key: str, value: str) -> dict:
        return {
            "match": {
                key: {
                    "query": value,
                    "fuzziness": "AUTO",
                    "prefix_length": 0
                }
            }
        }

    def build_search_query(self,
                           field: str,
                           musts: list = None,
                           shoulds: list = None,
                           filters: list = None,
                           query_return_length: int = 10):
        musts = musts or []
        shoulds = shoulds or []
        filters = filters or []
        query = {
            "size": query_return_length,
            "query": {
                "bool": {
                    "must": [self._match(field, m) for m in musts],
                    "should": [self._match(field, s) for s in shoulds],
                    "filter": filters
                }
            }
        }
        return json.dumps(query)
