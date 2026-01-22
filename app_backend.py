import pdfplumber
import os
import re
import json
from typing import List, Dict,Tuple
import requests
from io import BytesIO
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from langchain.text_splitter import RecursiveCharacterTextSplitter
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

system_prompt = (
    "You are an AI assistant that helps users understand the coverage, benefits, exclusions, and conditions of their health insurance policy, using only the provided policy document context.\n\n"
    "Users will ask natural language questions about specific treatments, benefits, waiting periods, or policy terms.\n\n"
    "Respond with the shortest accurate answer possible, strictly based on the document. Do not rely on external knowledge or make assumptions.\n\n"
    "If coverage depends on conditions such as time limits or eligibility, state them briefly. If a term is defined, summarize the definition clearly.\n\n"
    "Your response must:\n"
    "- Be in fluent, formal English\n"
    "- Fit within a single sentence on one line\n"
    "- Be concise, direct, and policy-specific\n"
    "- Avoid lists, bullet points, or extra formatting\n"
    "- Never repeat the user's question or include disclaimers\n"
    "- Only say 'not mentioned' if there is truly no relevant info in the context"
)

def download_pdf_from_url(url: str) -> BytesIO:
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: {response.status_code}")
    return BytesIO(response.content)

def smart_chunk_text(text: str, chunk_size=1000, chunk_overlap=200) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)

def extract_policy_name(text: str) -> str:
    matches = re.findall(r"\b(?:[A-Z][a-z]+\s?){1,6}Policy\b", text)
    blacklist = {"Policyholder", "Policy Terms", "Policy Document", "Policy Year", "Policy Period"}

    for match in matches:
        if all(bad not in match for bad in blacklist):
            return match.strip()

    return None

def extract_text_chunks_with_metadata(pdfurl, pdf_path: BytesIO, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
    chunks = []
    chunk_id = 0
    current_policy = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            cleaned_text = re.sub(r'\n+', ' ', text).strip()
            cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)

            detected_policy = extract_policy_name(cleaned_text)
            if detected_policy:
                current_policy = detected_policy

            chunked_texts = smart_chunk_text(cleaned_text, chunk_size, overlap)

            for chunk in chunked_texts:
                policy_tagged_chunk = f"[Policy: {current_policy}]\n{chunk}" if current_policy else chunk
                chunks.append({
                    "source": os.path.basename(urlparse(pdfurl).path),
                    "page": page_number,
                    "chunk_id": chunk_id,
                    "policy": current_policy,
                    "content": policy_tagged_chunk
                })
                chunk_id += 1

    return chunks

def embed_chunks_and_build_faiss_index(chunks: List[Dict], model) -> Tuple[np.ndarray, faiss.IndexFlatIP]:
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return embeddings, index

def retrieve_top_k_faiss(query: str, chunks: List[Dict], index: faiss.IndexFlatIP, model, top_k: int = 5) -> List[Dict]:
    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, indices = index.search(query_embedding, top_k)
    return [chunks[i] for i in indices[0]]

async def query_groq(question, context, model= "llama-3.3-70b-versatile"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 700
    }

    await asyncio.sleep(1.5)

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"Groq API error: {response.status_code}\n{response.text}")
    
    return response.json()["choices"][0]["message"]["content"]

def chat_with_policy(results, question):
    try:
        context = "\n\n".join([doc["content"] for doc in results])
        json_answer = query_groq(question, context)
        print(json_answer, "\n\n\n")
    except Exception as e:
        print("⚠ Error:", e)

