from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
import asyncio
import re

from app_backend import (
    download_pdf_from_url,
    extract_text_chunks_with_metadata,
    embed_chunks_and_build_faiss_index,
    retrieve_top_k_faiss,
    query_groq
)
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
security = HTTPBearer()


EXPECTED_BEARER = os.getenv("EXPECTED_BEARER")


class RAGRequest(BaseModel):
    documents: str  
    questions: List[str]

class RAGAnswer(BaseModel):
    question: str
    answer: str

class RAGResponse(BaseModel):
    answers: List[str]  


@app.post("/api/v1/hackrx/run", response_model=RAGResponse)
async def rag_endpoint(
    request_data: RAGRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if credentials.scheme != "Bearer" or credentials.credentials != EXPECTED_BEARER:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:

        pdf_file = download_pdf_from_url(request_data.documents)

        model = SentenceTransformer("all-MiniLM-L6-v2")
        chunks = extract_text_chunks_with_metadata(request_data.documents, pdf_file)
        embeddings, index = embed_chunks_and_build_faiss_index(chunks, model)

        answers_with_questions = []
        plain_answers = []

        for question in request_data.questions:
            while True:
                try:

                    top_chunks = retrieve_top_k_faiss(question, chunks, index, model, top_k=5)
                    context = "\n\n".join([c["content"] for c in top_chunks])

                    answer = await query_groq(question, context)
                    clean_answer = answer.strip()

                    answers_with_questions.append(RAGAnswer(question=question, answer=clean_answer))
                    plain_answers.append(clean_answer)
                    break 

                except Exception as e:
                    error_message = str(e)
                    if "rate_limit_exceeded" in error_message:

                        match = re.search(r"try again in ([0-9.]+)s", error_message)
                        if match:
                            delay = float(match.group(1)) + 0.5
                            print(f"Rate limit hit. Sleeping for {delay:.2f} seconds...")
                            await asyncio.sleep(delay)
                        else:
                            await asyncio.sleep(3)
                    else:
                        raise HTTPException(status_code=500, detail=f"Groq API error: {error_message}")

        return RAGResponse(answers=plain_answers)


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")