import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.embeddings import JinaEmbeddings
from supabase.client import Client, create_client
from dotenv import load_dotenv
from pprint import pprint
import re

base64_image_regex = re.compile(
    r'^(?:data:image\/[a-zA-Z]+;base64,)?([A-Za-z0-9+/]+={0,2})$'
)

def is_base64_image(s: str) -> bool:
    return bool(base64_image_regex.match(s))

load_dotenv()

SYSTEM_PROMPT = """
You are an **AI assistant** using **Retrieval-Augmented Generation (RAG)**.  
Your role is to give **accurate, concise, and well-structured answers** grounded in retrieved documents.  

## Core Rules
1. **Grounding**: Use retrieved docs as the main source and images if is attached. Quote, summarize, or synthesize fairly.  
2. **Reasoning**: Be logical and structured. If context is incomplete, acknowledge gaps; only add reliable general knowledge.  
3. **Transparency**: If unsure or context is insufficient, say so. Use phrases like *“Based on the retrieved docs…”*. Never hallucinate or invent citations.  
4. **Style**: Polite, professional, and clear. Use plain language; structure long answers with bullets or steps.  
5. **Guardrails**: Avoid harmful/biased content. Stay on-topic.  

"""

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

multimodal_embeddings = JinaEmbeddings(jina_api_key=os.environ.get("JINA_API_KEY"), model_name="jina-clip-v2")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.5, max_output_tokens=1024)

def retrieve_relevant_docs(query, top_k=5):
    """Retrieve relevant documents from Supabase using vector similarity search."""
    documents = []
    images = []
    query_embedding = multimodal_embeddings.embed_query(query)
    response = (
        supabase.rpc("match_documents", 
                     {"query_embedding": query_embedding, 
                      "match_threshold": 0.6, 
                      "match_count": top_k})
        .execute()
    )
    for doc in response.data:
        if is_base64_image(doc['content']):
            images.append(doc['content'])
        else:
            documents.append(doc['content'])
    return documents, images

def generate_answer(query, top_k=5):
    """Generate an answer using the LLM based on the query and retrieved documents."""
    documents, images = retrieve_relevant_docs(query, top_k)
    context = "\n\n".join(documents) if documents else "No relevant documents found."
    content = [{"type": "text", "text": f"Question: {query}\n\nRelevant context from documents:\n{context}"}]
    
    if images:
        for image in images:
            element= {
                "type": "image",
                "source_type": "base64",
                "data": image,
                "mime_type": "image/jpeg" if "jpeg" in image else "image/png"
            }
            content.append(element)

    messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    
    response = llm.invoke(messages)
    return response.text()
    

    
    
    
    

