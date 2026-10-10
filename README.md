\AI Assistant — Your Local Files, One Conversation Away



A Python-based desktop AI application that lets you interact with your videos, YouTube content, PDFs, and images through a conversational interface. Instead of manually searching through long documents or videos, you can ask questions and get answers based on the content you provide.



The application combines Retrieval-Augmented Generation (RAG), local language models, document processing, and speech transcription in a floating desktop interface.



\## What Can You Do With It?



\* \*\*Chat with YouTube videos:\*\* Extract available transcripts and ask questions about the video's content.

\* \*\*Chat with local videos:\*\* Transcribe supported video files using Whisper and ask questions about what was said.

\* \*\*Ask questions about PDFs:\*\* Extract document text and retrieve relevant information from your files.

\* \*\*Process scanned PDFs:\*\* Use optical character recognition (OCR) to extract text from scanned documents.

\* \*\*Work with images:\*\* Process image inputs supported by the application's image-processing workflow.

\* \*\*Get context-aware answers:\*\* Retrieve relevant information from your sources using a RAG pipeline before generating answers.

\* \*\*Use a local language model:\*\* Run a Qwen model locally through a `llama.cpp` server, reducing dependence on paid LLM APIs for the core chat workflow.

\* \*\*Reuse cached data:\*\* Avoid repeating certain transcription and extraction work when cached results are available.

\* \*\*Use a floating desktop interface:\*\* Interact with the assistant through a compact desktop UI instead of a command-line-only workflow.



\## It's a Desktop App



This project is designed to behave like a desktop application, with a graphical interface you can open and interact with on your computer.



\*\*Current distribution status:\*\* The application has been tested locally on Windows. A ready-to-use installer or downloadable packaged release is not currently provided by this repository.



You can run it from the Python source code after setting up the dependencies and models. A packaged Windows build can also be created using the included PyInstaller configuration.



\## How It Works



1\. \*\*Input:\*\* Provide a YouTube URL, a supported local video, a PDF, or an image.

2\. \*\*Extraction:\*\* The application retrieves available transcript text, transcribes audio, extracts PDF text, or processes supported image inputs.

3\. \*\*Retrieval:\*\* The RAG pipeline uses document embeddings and FAISS to find relevant content.

4\. \*\*Answer generation:\*\* A language model uses the retrieved context to generate a response.

5\. \*\*Conversation:\*\* Ask follow-up questions about the same source where the workflow supports it.



\## Technology Stack



\* \*\*Language:\*\* Python

\* \*\*Desktop GUI:\*\* PySide6

\* \*\*LLM orchestration:\*\* LangChain

\* \*\*Retrieval:\*\* FAISS

\* \*\*Embeddings:\*\* Hugging Face sentence-transformer model

\* \*\*Local LLM runtime:\*\* llama.cpp

\* \*\*Language model:\*\* Qwen GGUF

\* \*\*Audio transcription:\*\* Whisper

\* \*\*Video downloading:\*\* yt-dlp

\* \*\*PDF processing:\*\* PyMuPDF

\* \*\*OCR:\*\* PaddleOCR

\* \*\*Web search:\*\* DuckDuckGo Search and Tavily integration



\## Requirements



\* Windows

\* Python 3.13.2, the development environment used for testing

\* Required Python packages from `requirements.txt`

\* A local Qwen GGUF model and the llama.cpp runtime

\* The embedding model used by the RAG pipeline

\* Additional disk space and processing resources for transcription, embeddings, and OCR



\## Running the Application



The application currently requires a manual setup. Installation and execution instructions will be added after validating the dependency list and model setup on a clean environment.



\## Local Models and Privacy



The application supports a local language model for its core chat workflow. Model files and runtime binaries are not included in this repository because they are large.



Local processing can reduce the need to send document content to a hosted LLM, but external services may still be contacted for features such as web search or online transcript retrieval. Review the relevant service configurations before using sensitive documents.



Model licenses and third-party software licenses apply separately. Check them before redistributing model files or packaged builds.



\## Configuration and API Keys



Optional integrations may require environment variables, such as a Tavily API key for web search.



\* Keep API keys in a local `.env` file.

\* Never commit `.env` files, credentials, or private configuration to GitHub.

\* Some features may be unavailable when their external services are inaccessible or not configured.



\## Project Status



\*\*Working locally:\*\* Desktop interface, video transcription, YouTube transcript retrieval, PDF text extraction, scanned-PDF OCR, image processing, and local Qwen chat have been tested in the development environment.



Setup instructions and a reproducible packaged release are still being prepared.



\## License



No project license has been selected yet. Until a license is added, do not assume that the source code is licensed for unrestricted reuse or redistribution.
