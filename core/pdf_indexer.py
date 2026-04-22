import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from core.security_manager import SecurityManager

class PDFIndexer:
    """Handles indexing of PDF content for RAG."""
    
    def __init__(self):
        self.vector_store = None
        self.embeddings = None

    def initialize_embeddings(self, provider="openai"):
        """Initializes the embedding model based on provider."""
        api_key = SecurityManager.get_api_key(provider)
        if not api_key:
            return False
            
        if provider == "openai":
            self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        elif provider == "gemini":
            self.embeddings = GoogleGenerativeAIEmbeddings(google_api_key=api_key, model="models/embedding-001")
        else:
            return False
        return True

    def index_document(self, fitz_doc):
        """Indexes the text content of a fitz Document."""
        if not self.embeddings:
            if not self.initialize_embeddings():
                return False

        documents = []
        for page_num, page in enumerate(fitz_doc):
            text = page.get_text()
            if text.strip():
                documents.append(Document(
                    page_content=text,
                    metadata={"page": page_num, "source": "pdf"}
                ))

        if not documents:
            return False

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)

        # Create vector store
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
        return True

    def similarity_search(self, query, k=3):
        """Searches for relevant chunks."""
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k)
