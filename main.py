
from pathlib import Path
import pymupdf
import tempfile
from dotenv import load_dotenv
from pdf_processor import extract_pdf_text
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import (
    HuggingFaceEmbeddings
)
from langchain_openai import ChatOpenAI
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser

from audio_transcript import get_transcript, get_transcript_from_local
from extractor import extract_youtube_details, identify
from web_search import search


# Load environment variables, including API keys.
load_dotenv()

import sys
from pathlib import Path


def get_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent

# --------------------------------------------------
# 1. PROCESS A LOCAL VIDEO OR YOUTUBE URL
# --------------------------------------------------

def process_input(user):
    input_type, source = identify(user)

    if input_type == "local":
        source_id = Path(source).stem
        transcript = get_transcript_from_local(source)
        return transcript, source_id

    elif input_type == "url":
        video_url, source_id = extract_youtube_details(source)
        transcript = get_transcript(source_id, video_url)
        return transcript, source_id

    else:
        raise ValueError("The given video path or URL is invalid.")


# --------------------------------------------------
# 2. CREATE THE CHATBOT FOR THE SELECTED VIDEO
# --------------------------------------------------

def create_chatbot(transcript_segments, video_id):

    # Keep timestamps alongside the transcript text.
    transcript = "\n".join(
        f"[{segment['start']} - {segment['end']}] {segment['text']}"
        for segment in transcript_segments
    )

    print("Transcript loaded successfully.")

    # --------------------------------------------------
    # 1. SPLIT TRANSCRIPT
    # --------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.create_documents(
        [transcript]
    )

    # --------------------------------------------------
    # 2. EMBEDDINGS
    # --------------------------------------------------

    embedding_model = HuggingFaceEmbeddings(
        model_name=str(
        get_app_path() / "models" / "bge-small-en-v1.5"
    ),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # --------------------------------------------------
    # 3. LOAD OR CREATE FAISS
    # --------------------------------------------------

    project_folder = Path(__file__).resolve().parent

    index_folder = (
        project_folder
        / "vector_storage"
        / video_id
    )

    index_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    index_file = index_folder / "index.faiss"
    metadata_file = index_folder / "index.pkl"

    if index_file.exists() and metadata_file.exists():

        vector_store = FAISS.load_local(
            str(index_folder),
            embedding_model,
            allow_dangerous_deserialization=True
        )

        print(
            "FAISS vector store loaded successfully."
        )

    else:

        print(
            "Vectors not found. Generating vectors..."
        )

        vector_store = FAISS.from_documents(
            chunks,
            embedding=embedding_model
        )

        vector_store.save_local(
            str(index_folder)
        )

        print(
            "FAISS vector store created and saved."
        )

    # --------------------------------------------------
    # 4. RETRIEVER
    # --------------------------------------------------

    vector_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    # --------------------------------------------------
    # 5. LOCAL QWEN MODEL
    # --------------------------------------------------
    #
    # This connects LangChain to the local llama.cpp
    # server running at:
    #
    # http://127.0.0.1:8080
    #
    # No OpenAI API key is required.
    #

    local_llm = ChatOpenAI(
        model="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M",
        base_url="http://127.0.0.1:8080/v1",
        api_key="local",
        temperature=0.7,
        max_tokens=256
    )

    # --------------------------------------------------
    # 6. CONTEXTUAL COMPRESSION
    # --------------------------------------------------

    compressor_llm = ChatOpenAI(
        model="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M",
        base_url="http://127.0.0.1:8080/v1",
        api_key="local",
        temperature=0,
        max_tokens=100
    )

    compressor = LLMChainExtractor.from_llm(
        compressor_llm
    )

    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=vector_retriever
    )

    # --------------------------------------------------
    # 7. CREATE TRANSCRIPT CONTEXT
    # --------------------------------------------------

    def context(retrieved_text):

        combined_context = "\n\n".join(
            doc.page_content
            for doc in retrieved_text
        )

        print(
            "Transcript context creation successful."
        )

        return combined_context

    # --------------------------------------------------
    # 8. QUESTION REWRITER
    # --------------------------------------------------

    rewrite_prompt = PromptTemplate(
        template="""<|system|>
You rewrite the user's current question into a standalone question.

Use the conversation history to resolve references such as:
"it", "they", "that", "this", or "the previous answer".

If the question is already standalone, return it unchanged.

Return ONLY the rewritten question.
Do not explain your changes.
</|system|>

<|user|>
Conversation history:
{chat_history}

Current question:
{question}
</user>

<|assistant|>
""",
        input_variables=[
            "question",
            "chat_history"
        ]
    )

    rewrite_chain = (
        rewrite_prompt
        | local_llm
        | StrOutputParser()
    )

    # --------------------------------------------------
    # 9. FINAL ANSWER PROMPT
    # --------------------------------------------------

    prompt = PromptTemplate(
        template="""<|system|>
You are a helpful assistant. You will receive a YouTube
transcript context, web search results, conversation history,
and a question.

Provide TWO separate answers:

1. YouTube Transcript Answer:
- Answer using only the provided transcript context.
- If the answer is not available in the transcript,
  say "I don't know based on the transcript."

2. Web Search Answer:
- Answer using only the provided web search results.
- If the results do not contain enough information,
  say "I don't know based on the web search results."

Keep both answers short, direct, and clearly separated.
Do not invent information.
Do not use web search results for the transcript answer.
Do not use the transcript context for the web answer.

Use the conversation history only to understand
what the current question refers to.

</|system|>

<|user|>
Conversation history:
{chat_history}

YouTube transcript context:
{context}

Web search results:
{web_result}

Current question:
{question}

Provide both answers using the rules above.
</user>

<|assistant|>
""",
        input_variables=[
            "question",
            "context",
            "web_result",
            "chat_history"
        ]
    )

    parser = StrOutputParser()

    # --------------------------------------------------
    # 10. REWRITE QUESTION USING CHAT HISTORY
    # --------------------------------------------------

    def rewrite_question(x):

        rewritten_question = rewrite_chain.invoke({
            "question": x["question"],
            "chat_history": x["chat_history"]
        })

        print(
            "Rewritten question:",
            rewritten_question
        )

        return rewritten_question

    # --------------------------------------------------
    # 11. RETRIEVE TRANSCRIPT + WEB RESULTS
    # --------------------------------------------------

    parallel_chain = RunnableParallel({

        # Send the rewritten question to the final prompt.
        "question": RunnableLambda(
            rewrite_question
        ),

        # Keep the conversation history for the final prompt.
        "chat_history": RunnableLambda(
            lambda x: x["chat_history"]
        ),

        # Use the rewritten question for transcript retrieval.
        "context": (
            RunnableLambda(
                rewrite_question
            )
            | retriever
            | RunnableLambda(context)
        ),

        # Use the rewritten question for web search.
        "web_result": (
            RunnableLambda(
                rewrite_question
            )
            | RunnableLambda(search)
        )
    })

    # --------------------------------------------------
    # 12. FINAL CHAIN
    # --------------------------------------------------

    main_chain = (
        parallel_chain
        | prompt
        | local_llm
        | parser
    )

    return main_chain


# --------------------------------------------------
# 3. CONVERT IMAGE TO TEMPORARY PDF
# --------------------------------------------------

def convert_image_to_pdf(image_path):

    image_document = pymupdf.open(image_path)

    pdf_bytes = image_document.convert_to_pdf()

    image_document.close()

    temporary_pdf = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    )

    temporary_pdf.write(pdf_bytes)
    temporary_pdf.close()

    return temporary_pdf.name
def create_pdf_chatbot(pdf_text, pdf_id):

    print("PDF text loaded successfully.")

    # --------------------------------------------------
    # 1. SPLIT PDF TEXT
    # --------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.create_documents(
        [pdf_text]
    )

    # --------------------------------------------------
    # 2. EMBEDDINGS
    # --------------------------------------------------

    embedding_model = HuggingFaceEmbeddings(
        model_name=str(
        get_app_path() / "models" / "bge-small-en-v1.5"
    ),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # --------------------------------------------------
    # 3. LOAD OR CREATE FAISS
    # --------------------------------------------------

    project_folder = Path(__file__).resolve().parent

    index_folder = (
        project_folder
        / "vector_storage"
        / "pdf"
        / pdf_id
    )

    index_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    index_file = index_folder / "index.faiss"
    metadata_file = index_folder / "index.pkl"

    if index_file.exists() and metadata_file.exists():

        vector_store = FAISS.load_local(
            str(index_folder),
            embedding_model,
            allow_dangerous_deserialization=True
        )

        print(
            "PDF FAISS vector store loaded successfully."
        )

    else:

        print(
            "PDF vectors not found. Generating vectors..."
        )

        vector_store = FAISS.from_documents(
            chunks,
            embedding=embedding_model
        )

        vector_store.save_local(
            str(index_folder)
        )

        print(
            "PDF FAISS vector store created and saved."
        )

    # --------------------------------------------------
    # 4. RETRIEVER
    # --------------------------------------------------

    vector_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    # --------------------------------------------------
    # 5. LOCAL QWEN MODEL
    # --------------------------------------------------
    #
    # This connects LangChain to the local llama.cpp
    # server running at:
    #
    # http://127.0.0.1:8080
    #
    # No OpenAI API key is required.
    #

    local_llm = ChatOpenAI(
        model="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M",
        base_url="http://127.0.0.1:8080/v1",
        api_key="local",
        temperature=0.7,
        max_tokens=256
    )

    # --------------------------------------------------
    # 6. CONTEXTUAL COMPRESSION
    # --------------------------------------------------

    compressor_llm = ChatOpenAI(
        model="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M",
        base_url="http://127.0.0.1:8080/v1",
        api_key="local",
        temperature=0,
        max_tokens=100
    )

    compressor = LLMChainExtractor.from_llm(
        compressor_llm
    )

    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=vector_retriever
    )

    # --------------------------------------------------
    # 7. CREATE PDF CONTEXT
    # --------------------------------------------------

    def context(retrieved_text):

        combined_context = "\n\n".join(
            doc.page_content
            for doc in retrieved_text
        )

        print(
            "PDF context creation successful."
        )

        return combined_context

    # --------------------------------------------------
    # 8. QUESTION REWRITER
    # --------------------------------------------------

    rewrite_prompt = PromptTemplate(
        template="""<|system|>
You rewrite the user's current question into a standalone question.

Use the conversation history to resolve references such as:
"it", "they", "that", "this", or "the previous answer".

If the question is already standalone, return it unchanged.

Return ONLY the rewritten question.
Do not explain your changes.
</|system|>

<|user|>
Conversation history:
{chat_history}

Current question:
{question}
</user>

<|assistant|>
""",
        input_variables=[
            "question",
            "chat_history"
        ]
    )

    rewrite_chain = (
        rewrite_prompt
        | local_llm
        | StrOutputParser()
    )

    # --------------------------------------------------
    # 9. FINAL ANSWER PROMPT
    # --------------------------------------------------

    prompt = PromptTemplate(
        template="""<|system|>
You are a helpful assistant. You will receive a PDF document context,
web search results, conversation history, and a question.

Provide TWO separate answers:

1. PDF Document Answer:
- Answer using only the provided PDF context.
- If the answer is not available in the PDF context,
  say "I don't know based on the PDF."

2. Web Search Answer:
- Answer using only the provided web search results.
- If the results do not contain enough information,
  say "I don't know based on the web search results."

Keep both answers short, direct, and clearly separated.
Do not invent information.
Do not use web search results for the PDF answer.
Do not use the PDF context for the web answer.

Use the conversation history only to understand
what the current question refers to.

</|system|>

<|user|>
Conversation history:
{chat_history}

PDF context:
{context}

Web search results:
{web_result}

Current question:
{question}

Provide both answers using the rules above.
</user>

<|assistant|>
""",
        input_variables=[
            "question",
            "context",
            "web_result",
            "chat_history"
        ]
    )

    parser = StrOutputParser()

    # --------------------------------------------------
    # 10. REWRITE QUESTION
    # --------------------------------------------------

    def rewrite_question(x):

        rewritten_question = rewrite_chain.invoke({
            "question": x["question"],
            "chat_history": x["chat_history"]
        })

        print(
            "Rewritten question:",
            rewritten_question
        )

        return rewritten_question

    # --------------------------------------------------
    # 11. RETRIEVE PDF + WEB RESULTS
    # --------------------------------------------------

    parallel_chain = RunnableParallel({

        "question": RunnableLambda(
            rewrite_question
        ),

        "chat_history": RunnableLambda(
            lambda x: x["chat_history"]
        ),

        "context": (
            RunnableLambda(
                rewrite_question
            )
            | retriever
            | RunnableLambda(context)
        ),

        "web_result": (
            RunnableLambda(
                rewrite_question
            )
            | RunnableLambda(search)
        )
    })

    # --------------------------------------------------
    # 12. FINAL CHAIN
    # --------------------------------------------------

    main_chain = (
        parallel_chain
        | prompt
        | local_llm
        | parser
    )

    return main_chain


# --------------------------------------------------
# 5. TERMINAL MODE
# Runs only when main.py is executed directly.
# Importing main.py from the UI will not start this.
# --------------------------------------------------

if __name__ == "__main__":

    pdf_path = "C:\\Users\\78794\\Downloads\\pymupdf_rag_test.pdf"

    pdf_text = extract_pdf_text(pdf_path)

    pdf_id = Path(pdf_path).stem

    main_chain = create_pdf_chatbot(
        pdf_text,
        pdf_id
    )

    while True:

        question = input(
            "\nGive your query related to the PDF "
            "(or type 'exit'): "
        )

        if question.strip().lower() == "exit":
            break

        # The chain expects the question and chat history.
        result = main_chain.invoke({
            "question": question,
            "chat_history": ""
        })

        print("\n", result)