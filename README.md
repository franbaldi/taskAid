# WhatsApp Chatbot with Naive RAG Implementation

This project implements a WhatsApp chatbot using a naive Retrieval-Augmented Generation (RAG) approach. It leverages the FARM stack (FastAPI, MongoDB, and optionally React), Twilio for WhatsApp messages, OLLama for local LLM processing, and Ngrok for tunneling.

## Features

- Process incoming WhatsApp messages via Twilio webhooks.
- Embed user queries and perform vector search against MongoDB-stored document embeddings.
- Generate dynamic responses using a locally hosted OLLama server.
- Easily update document embeddings using the provided script.

## Project Structure

