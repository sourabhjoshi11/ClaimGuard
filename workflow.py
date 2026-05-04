from langgraph.graph import StateGraph, END

from validate import input_validation_node
from valuation import valuation_node
from comparision import comparison_node
from state import ClaimState


def after_validation(state: ClaimState):
    return "continue" if state.get("is_image_clear") else "stop"


def after_comparison(state: ClaimState):
    return "estimate" if state.get("status") == "Groq Comparison Done" else "stop"


workflow = StateGraph(ClaimState)

workflow.add_node("validate_image", input_validation_node)
workflow.add_node("compare_asset", comparison_node)
workflow.add_node("estimate_cost", valuation_node)

workflow.set_entry_point("validate_image")

workflow.add_conditional_edges(
    "validate_image",
    after_validation,
    {
        "continue": "compare_asset",
        "stop": END,
    },
)

workflow.add_conditional_edges(
    "compare_asset",
    after_comparison,
    {
        "estimate": "estimate_cost",
        "stop": END,
    },
)

workflow.add_edge("estimate_cost", END)

app = workflow.compile()




