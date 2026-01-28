import os
from typing import List, TypedDict, Dict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

load_dotenv()

# --- Dependencies (Models) ---
# Using the key/base from the app.py configuration for consistency
llm = ChatOpenAI(
    model="gpt-4-turbo",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db_client = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "chroma_db_video"))
video_collection = db_client.get_or_create_collection(
    name=os.getenv("CHROMA_DB_COLLECTION", "video_collection"),
    metadata={"hnsw:space": "cosine"}
)

# --- State ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    video_id: str
    documents: List[str]
    metadata: List[Dict]
    generation: str
    decision: str

# --- Nodes ---

def agent_brain(state: AgentState):
    """Decides initial route."""
    print("🤔 Entering Agent Brain...")
    if not state.get("documents"):
        return {"decision": "retrieve"}
    return {"decision": "generate"}

def retrieve_tool(state: AgentState):
    print("🔍 Entering Retrieve Tool (Multimodal)...")
    user_query = state['messages'][-1].content
    video_id = state['video_id']

    query_embedding = embedding_model.embed_query(user_query)
    results = video_collection.query(
        query_embeddings=[query_embedding],
        n_results=10, # Increased for multimodal variety
        where={"video_id": video_id}
    )

    docs = results['documents'][0] if results['documents'] else []
    metas = results['metadatas'][0] if results['metadatas'] else []
    print(f"\t- Retrieved {len(docs)} context blocks.")

    return {"documents": docs, "metadata": metas}

def grade_documents(state: AgentState):
    print("🧐 Entering Grade Documents...")
    user_query = state['messages'][-1].content
    documents = state['documents']

    if not documents:
        return {"decision": "rewrite"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Determine if the following video snippets are relevant to the user's question. Respond with 'yes' or 'no'."),
        ("human", "Question: {user_query}\n\nSnippets:\n{documents}")
    ])
    chain = prompt | llm
    response = chain.invoke({"user_query": user_query, "documents": "\n\n".join(documents[:3])})

    if "yes" in response.content.lower():
        return {"decision": "generate"}
    return {"decision": "rewrite"}

def generate_answer(state: AgentState):
    print("💬 Entering Generate Answer (Multimodal)...")

    # Format context with source types and timestamps
    context_parts = []
    for doc, meta in zip(state.get('documents', []), state.get('metadata', [])):
        source_type = meta.get('type', 'info').upper()
        timestamp = meta.get('timestamp_formatted', '?')
        context_parts.append(f"[{source_type} at {timestamp}] {doc}")

    context = "\n\n".join(context_parts)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are "VideoBrain", an expert analyzing a video using both visual frame descriptions and audio transcripts.

Answer based ONLY on the provided context below. The context includes timestamps showing when things were seen [VISUAL] or heard [AUDIO].

IMPORTANT: Provide a natural, flowing response that synthesizes information from both visual and audio sources. Do NOT include citation markers like [VISUAL at M:SS] or [AUDIO at M:SS] in your response. Instead, naturally mention timing when relevant (e.g., "At the beginning of the video..." or "Around 30 seconds in...").

If the information isn't available in the context, say you don't know."""),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "CONTEXT FROM VIDEO (Visuals & Audio):\n\n{context}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "messages": state['messages'],
        "context": context
    })
    return {"generation": response.content}

def rewrite_query(state: AgentState):
    print("✍️ Entering Rewrite Query...")
    user_query = state['messages'][-1].content
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Rephrase the search query for better multimodal retrieval from video transcripts and descriptions."),
        ("human", "Original: {user_query}")
    ])
    chain = prompt | llm
    response = chain.invoke({"user_query": user_query})

    new_messages = list(state['messages'])
    new_messages[-1] = HumanMessage(content=response.content)
    return {"messages": new_messages}

# --- Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("agent_brain", agent_brain)
workflow.add_node("retrieve_tool", retrieve_tool)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("rewrite_query", rewrite_query)
workflow.add_node("generate_answer", generate_answer)

workflow.set_entry_point("agent_brain")

def check_decision(state: AgentState):
    return state.get("decision", "retrieve")

workflow.add_conditional_edges(
    "agent_brain",
    check_decision,
    {"retrieve": "retrieve_tool", "generate": "generate_answer"}
)

workflow.add_edge("retrieve_tool", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    check_decision,
    {"generate": "generate_answer", "rewrite": "rewrite_query"}
)

workflow.add_edge("rewrite_query", "retrieve_tool")
workflow.add_edge("generate_answer", END)

memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)

# Helper to run the agent
def invoke_agent(user_message: str, video_id: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {
        "messages": [HumanMessage(content=user_message)],
        "video_id": video_id,
        "documents": [],
        "metadata": [],
        "generation": ""
    }
    final_state = agent_app.invoke(inputs, config)
    return final_state['generation']
