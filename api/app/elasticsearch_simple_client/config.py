import os


class Config:
    def __init__(self):
        self.es_batch_size = None
        self.es_url = None
        self.query_return_length = None
        self.es_index = None

    @classmethod
    def default(cls):
        output = cls()
        output.es_url = "http://elasticsearch:9200/" if os.environ.get("ES_URL") is None else os.environ["ES_URL"]
        output.query_return_length = 1 if os.environ.get("QUERY_RETURN_LENGTH") is None else os.environ[
            "QUERY_RETURN_LENGTH"]
        output.es_index = "transactions" if os.environ.get("ES_INDEX") is None else os.environ["ES_INDEX"]

        return output
