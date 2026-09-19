from typing import TypedDict, List, Annotated, Literal
import operator
from pydantic import BaseModel, Field

# ==========================================
# 1. Pydantic Schemas for Tool Validation
# ==========================================

class CreateInvoiceSchema(BaseModel):
    recipient_email: str = Field(description="The email address of the invoice recipient.")
    amount: float = Field(description="The total monetary amount for the invoice.")
    currency: str = Field(default="USD", description="Currency code, e.g., USD, EUR.")

class DisputeSchema(BaseModel):
    user_id: str = Field(description="The user ID to check for open disputes.")

# ==========================================
# 2. Mock Tool Implementations (PayPal + RAG + System Search)
# ==========================================

def paypal_create_invoice(args: CreateInvoiceSchema):
    """Simulates creating an invoice via PayPal API."""
    return {
        "status": "success",
        "invoice_id": "INV-98765",
        "recipient": args.recipient_email,
        "amount": args.amount,
        "currency": args.currency
    }

def paypal_get_dispute(args: DisputeSchema):
    """Simulates checking a dispute for a specific user."""
    return {
        "status": "success",
        "user_id": args.user_id,
        "dispute_open": True,
        "dispute_id": "DSP-456"
    }

def rag_pipeline_tool(query: str):
    """Queries product documentation or guides."""
    return {
        "source": "knowledge_base",
        "answer": f"Relevant documentation found for query: '{query}'."
    }

def system_search_tool(query: str):
    """Searches system capabilities and logs."""
    return {
        "source": "system_logs",
        "result": f"System capability matched for: '{query}'."
    }

# ==========================================
# 3. LangGraph State & Node Definitions
# ==========================================

class AgentState(TypedDict):
    messages: Annotated[List[str], operator.add]
    current_intent: str
    retrieved_tools: List[str]
    execution_result: str

def router_node(state: AgentState):
    """
    Simulates querying a Vector DB to retrieve the top-k relevant tools 
    from a large collection (500+ APIs) to prevent context degradation.
    """
    latest_message = state["messages"][-1].lower()
    
    if "invoice" in latest_message:
        tools = ["paypal_create_invoice"]
        intent = "billing"
    elif "dispute" in latest_message:
        tools = ["paypal_get_dispute"]
        intent = "disputes"
    elif "tool" in latest_message or "status" in latest_message:
        tools = ["system_search_tool"]
        intent = "system_search"
    else:
        tools = ["rag_pipeline_tool"]
        intent = "rag"
        
    print(f"[Router Node] Intent identified: '{intent}' -> Retrieved tools: {tools}")
    return {
        "retrieved_tools": tools,
        "current_intent": intent
    }

def execution_node(state: AgentState):
    """
    Executes the matched tool using validated parameters.
    """
    tools = state["retrieved_tools"]
    latest_msg = state["messages"][-1]
    
    print(f"[Execution Node] Executing tools: {tools}")
    
    if "paypal_create_invoice" in tools:
        args = CreateInvoiceSchema(recipient_email="test@example.com", amount=50.0)
        result = paypal_create_invoice(args)
    elif "paypal_get_dispute" in tools:
        args = DisputeSchema(user_id="user_123")
        result = paypal_get_dispute(args)
    elif "system_search_tool" in tools:
        result = system_search_tool(latest_msg)
    else:
        result = rag_pipeline_tool(latest_msg)
        
    return {"execution_result": str(result)}

# ==========================================
# 4. Main Execution Entrypoint
# ==========================================

if __name__ == "__main__":
    print("--- Scalable Agentic System Mock Run ---")
    
    test_queries = [
        "Send an invoice for $50 to test@example.com",
        "Is there a dispute open from user_123?",
        "What tools are available for managing invoices?"
    ]
    
    for query in test_queries:
        print(f"\nUser Input: '{query}'")
        
        initial_state = {
            "messages": [query],
            "current_intent": "",
            "retrieved_tools": [],
            "execution_result": ""
        }
        
        route_output = router_node(initial_state)
        initial_state.update(route_output)
        
        exec_output = execution_node(initial_state)
        initial_state.update(exec_output)
        
        print(f"Final Output: {initial_state['execution_result']}")
