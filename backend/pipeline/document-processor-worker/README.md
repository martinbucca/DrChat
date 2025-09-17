# Document Processor Worker

This service is responsible for receiving documents and processing them into a graph structure. It is a core component of the document processing pipeline.

## Features

- **Document Ingestion:** Receives and manages incoming documents.
- **Chunking:** Splits documents into manageable chunks for efficient processing.
- **Embeddings Generation:** Creates vector embeddings for each chunk to enable semantic analysis.
- **Entity & Relationship Extraction:** Identifies entities and their relationships within the document content.
- **Graph Loading:** Loads the extracted data into a graph database for downstream applications.

## Usage
