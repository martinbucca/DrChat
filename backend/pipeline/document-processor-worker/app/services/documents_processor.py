import os
import time

class DocumentsProcessor:
    """
    DocumentsProcessor is a singleton class responsible for processing a list of document files.
    It utilizes a chunker to split documents into smaller pieces and a graph builder to process and store these chunks in a graph database.
    Attributes:
        chunker: An object responsible for chunking documents.
        graph_builder: An object responsible for processing and storing document chunks in a graph database.
    Methods:
        process_files(filepaths: list[str]):
            Processes each file in the provided list by chunking and storing its contents.
            Prints progress and timing information for each file and the total processing time.
        get_instance(chunker, graph_builder):
            Returns the singleton instance of DocumentsProcessor, creating it if it does not exist.
    """

    _instance = None

    def __init__(self, chunker, graph_builder):
        self.chunker = chunker
        self.graph_builder = graph_builder

    # Procesar esto en paralelo (?)
    def process_file(self, filepath: str):
        start_time = time.time()
        filename = os.path.basename(filepath)
        print(f"Processing {filename}...")
        chunks = self.chunker.chunk_document(filepath, filename)
        print(f" - Chunked into {len(chunks)} pieces.")
        self.graph_builder.process_chunks(chunks)
        print(f" - Processed and stored in graph database.")
        elapsed = time.time() - start_time
        print(f"Time to process {filename}: {int(elapsed // 60)}m {elapsed % 60:.2f}s")

    @classmethod
    def get_instance(cls, chunker, graph_builder):
        if cls._instance is None:
            cls._instance = cls(chunker, graph_builder)
        return cls._instance
