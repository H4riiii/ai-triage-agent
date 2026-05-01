from pydantic import BaseModel, Field
from typing import Literal

class TicketTriage(BaseModel):
    status: Literal["replied", "escalated"] = Field(description = "Action taken on the ticket")
    product_area : str = Field(description = "The specific domain or category of the product issue")
    response: str = Field(description = "The user-facing response grounded ONLY in the corpus")
    justification: str = Field(description = "Brief explanation of why this decision was made")
    request_type: Literal["product_issue", "feature_request", "bug", "invalid"] = Field(description="Categorization of the request")