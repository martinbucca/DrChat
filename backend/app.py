from create_knowledge_graph import KnowledgeGraphBuilder
from vector_rag import VectorRetriever
class App:
    def __init__(self):
        self.knowledge_graph_builder = None
        self.vector_retriever = None

    def create_knowledge_graph(self):
        try:
            self.knowledge_graph_builder = KnowledgeGraphBuilder()
            self.knowledge_graph_builder.create_kg()
            self.create_vector_index()
        except Exception as e:
            print(e)
            raise e
    
    def create_vector_index(self):
        try:
            self.vector_retriever = VectorRetriever()
        except Exception as e:
            print(e)
            raise e
    
    def answer_query(self, query):
        try:
            if self.vector_retriever is None:
                self.create_vector_index()
            return self.vector_retriever.answer_with_rag(query)
        except Exception as e:
            print(e)
            raise e