from langchain_core.pydantic_v1 import BaseModel, Field

class Route(BaseModel):
    """Route to a destination based on a question and available routes."""
    destination: str = Field(..., description="Destination to route to")