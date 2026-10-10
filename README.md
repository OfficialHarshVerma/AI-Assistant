AI Assistant — Your Local Files, One Conversation Away

A Python desktop application that lets you ask questions about YouTube videos, local videos, PDFs, and images through a chat interface.

The idea is simple: instead of searching through a long video or document yourself, you can ask a question and get an answer based on its content.

The app uses Retrieval-Augmented Generation (RAG), local language models, speech transcription, and document processing.

Features

- Chat with YouTube videos using available transcripts.
- Transcribe local video files with Whisper and ask questions about their content.
- Extract text from PDFs and retrieve relevant information.
- Process scanned PDFs using OCR.
- Process supported image inputs.
- Retrieve relevant content with FAISS and document embeddings before generating answers.
- Run a local Qwen language model through llama.cpp for the core chat workflow.
- Reuse cached transcripts and extracted data when available.
- Use the assistant through a floating PySide6 desktop interface.

Desktop Application

The application has been tested locally on Windows.

It currently runs from Python source code after the required dependencies and models have been set up. The repository does not yet include a ready-to-use installer or downloadable packaged release.

The included PyInstaller configuration can be used to build a Windows application.

How It Works

1. Provide a YouTube URL, local video, PDF, or supported image.
2. The application extracts text, retrieves a transcript, transcribes audio, or processes the input.
3. The RAG pipeline uses embeddings and FAISS to find relevant content.
4. The language model generates an answer using the retrieved context.
5. Ask follow-up questions about the same source where supported.

Technology Stack

* Python
* PySide6
* LangChain
* FAISS
* Hugging Face sentence-transformers
* llama.cpp
* Qwen GGUF
* Whisper
* yt-dlp
* PyMuPDF
* PaddleOCR
* DuckDuckGo Search
* Tavily

Requirements

- Windows
- Python 3.13.2 (the version used during development)
- Dependencies listed in `requirements.txt`
- A compatible Qwen GGUF model
- The llama.cpp runtime
- The embedding model used by the RAG pipeline
- Additional disk space and processing resources for transcription, embeddings, and OCR

Setup

Setup currently requires manual installation of the dependencies and models. Step-by-step installation and execution instructions will be added after the dependency list and model setup have been validated in a clean environment.

Local Models and Privacy

The core chat workflow supports a local language model. Model files and runtime binaries are excluded from the repository because of their size.

Using a local model can reduce the need to send document content to a hosted language model. However, features such as web search and online transcript retrieval may contact external services. Check the configuration of these features before working with sensitive documents.

Third-party software and model licenses apply separately. Review the relevant licenses before redistributing models or packaged builds.

Configuration

Some integrations may require environment variables, such as a Tavily API key for web search.

- Store API keys in a local `.env` file.
- Do not commit `.env` files or credentials to GitHub.
- External integrations may not work when their services are unavailable or their configuration is missing.

Project Status

The desktop interface, video transcription, YouTube transcript retrieval, PDF extraction, scanned-PDF OCR, image processing, and local Qwen chat have been tested in the development environment.

Setup instructions and a reproducible packaged release are still in progress.

License

No project license has been selected yet. Until one is added, reuse and redistribution should not be assumed to be permitted.
