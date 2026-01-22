# BajajFinserv_project_LeaveItToUS

title: Bajaj Finserv Project
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
Team name: LEAVE IT TO US

Bajaj Finserv Mediclaim Policy Queries Chatbot :
            A document-based question-answering system built using RAG (Retrieval-Augmented Generation), FastAPI, Sentence Transformers, ChromaDB, and Groq LLM. This project allows users to provide policy or PDF documents via a link and ask relevant questions. The system retrieves the most relevant content from the document and provides precise answers using a language model.

Features

* Provide a document URL (PDF) as input.

* Ask multiple questions related to the document.

* Fast and accurate RAG-based answers.

* Supports any publicly accessible document.

* Answers are returned in a structured JSON format.

* Secured using Bearer Token authentication.

📄 Reference Input Example

You can send a POST request with a JSON body like this:

{ 
  "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D", 
  "questions": [ "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?", 
                  "What is the waiting period for pre-existing diseases (PED) to be covered?", "Does this policy cover maternity expenses, and what are the conditions?", 
                  "What is the waiting period for cataract surgery?", "Are the medical expenses for an organ donor covered under this policy?", 
                  "What is the No Claim Discount (NCD) offered in this policy?", "Is there a benefit for preventive health check-ups?", 
                  "How does the policy define a 'Hospital'?", 
                  "What is the extent of coverage for AYUSH treatments?", 
                  "Are there any sub-limits on room rent and ICU charges for Plan A?"
              ]
}

How to Use: 

* Access the deployed webhook URL:

POST (https://raghul12345678-leave-it-to-us-project.hf.space/api/v1/hackrx/run)

* Headers:

GROQ_API_KEY : EXPECTED_BEARER : 0004c0022fc653655fee5944e32fb4cfca4713b255a6f2c9ce19372915d6f28d

note : this only gives you access the send query

* Body: Use the JSON input as shown in the Reference Input Example.

* Receive answers: The response will be a JSON array with answers corresponding to the questions provided.

Notes :

* The system uses RAG (Retrieval-Augmented Generation) to combine:

* Document embeddings with Sentence Transformers.

* FAISS/ChromaDB vector store to retrieve the most relevant chunks.

* Groq LLM for generating the final answers.

* Works for any policy, medical, or legal document in PDF format.

Ensure the document is accessible via a public URL; private storage may require additional setup.
