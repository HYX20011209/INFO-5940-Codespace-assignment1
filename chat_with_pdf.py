import streamlit as st
import os
import tempfile
from openai import OpenAI
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

st.set_page_config(page_title="RAG Document Q&A", page_icon="📚", layout="wide")

st.title("RAG Document Question Answering System")
st.markdown("Upload documents (.txt or .pdf) and ask questions about their content.")

@st.cache_resource
def get_llm():
    return ChatOpenAI(
        api_key=os.environ.get("API_KEY"),
        base_url="https://api.ai.it.cornell.edu",
        model="openai.gpt-4o",
        temperature=0.2
    )

def load_documents(uploaded_files):
    """Load documents from uploaded files"""
    all_documents = []
    
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            if uploaded_file.name.endswith('.txt'):
                loader = TextLoader(tmp_file_path, encoding='utf-8')
            elif uploaded_file.name.endswith('.pdf'):
                loader = PyPDFLoader(tmp_file_path)
            else:
                st.warning(f"Unsupported file type: {uploaded_file.name}")
                continue
            
            documents = loader.load()
            
            for doc in documents:
                doc.metadata['source_file'] = uploaded_file.name
            
            all_documents.extend(documents)
            
        except Exception as e:
            st.error(f"Error loading {uploaded_file.name}: {str(e)}")
        finally:
            os.unlink(tmp_file_path)
    
    return all_documents

def process_documents(documents):
    """Chunk documents and create vector store"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings(
        model="openai.text-embedding-3-large"
    )
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    
    return vectorstore, len(chunks)

def retrieve_and_generate(question, vectorstore, llm):
    """Retrieve relevant chunks and generate answer"""
    retrieved_docs = vectorstore.similarity_search(question, k=5)
    
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    template = """You are a helpful assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
If you don't know the answer based on the context, just say that you don't know. Keep the answer concise and accurate.

Question: {question}

Context: {context}

Answer:"""
    
    prompt = PromptTemplate.from_template(template)
    messages = prompt.invoke({"question": question, "context": context})
    
    response = llm.invoke(messages)
    
    return response.content, retrieved_docs

with st.sidebar:
    st.header("Document Upload")
    
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        help="Upload one or more .txt or .pdf files"
    )
    
    if uploaded_files:
        st.subheader("Uploaded Files:")
        for file in uploaded_files:
            st.write(f"• {file.name}")
        
        if st.button("Process Documents", type="primary"):
            with st.spinner("Processing documents..."):
                documents = load_documents(uploaded_files)
                
                if documents:
                    vectorstore, num_chunks = process_documents(documents)
                    st.session_state.vectorstore = vectorstore
                    st.session_state.num_chunks = num_chunks
                    st.session_state.processed_files = [f.name for f in uploaded_files]
                    st.success(f"Processed {len(documents)} documents into {num_chunks} chunks!")
                else:
                    st.error("No documents were successfully loaded.")
    
    st.divider()
    
    if "vectorstore" in st.session_state:
        st.success("Documents ready for questions")
        st.info(f"Chunks: {st.session_state.num_chunks}")
        
        if st.button("Clear Documents"):
            del st.session_state.vectorstore
            del st.session_state.num_chunks
            del st.session_state.processed_files
            st.rerun()
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "vectorstore" not in st.session_state:
    st.info("Please upload and process documents using the sidebar to get started.")
else:
    st.success(f"Ready to answer questions about: {', '.join(st.session_state.processed_files)}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input(
    "Ask a question about your documents...",
    disabled="vectorstore" not in st.session_state
):
    st.session_state.messages.append({"role": "user", "content": question})
    
    with st.chat_message("user"):
        st.markdown(question)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                llm = get_llm()
                answer, sources = retrieve_and_generate(
                    question,
                    st.session_state.vectorstore,
                    llm
                )
                
                st.markdown(answer)
                
                with st.expander("View Sources"):
                    for i, doc in enumerate(sources, 1):
                        st.markdown(f"**Source {i}** (from {doc.metadata.get('source_file', 'unknown')})")
                        st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                        st.divider()
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})