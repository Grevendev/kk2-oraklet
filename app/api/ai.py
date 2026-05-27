# app/api/ai.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.chain.pipeline import pipeline

from app.state import state # global in-memory state (stats cached here)
from app.chain.steps import (
  PromptBuilder,
  LLMRunner,
  ResponseParser,
  PromptBuilderInput
)

router = APIRouter(prefix="/ai", tags=["AI"])

# Request model

class AskRequest(BaseModel):
  question: str


# /ai/ask endpoint

@router.post("/ask")
def ask_ai(request: AskRequest):
  """
  Executes the full Runnable chain:
  1. Validate that dataset stats exist
  2. Build prompt
  3. Run LLM
  4. Parse response
  5. Return structured output
  """

  # 1. Ensure stats exist
  if state.stats is None:
    raise HTTPException(
      status_code=400,
      detail="No dataset uploaded. Upload data before asking questions."
    )
  
  # 2. Build prompt
  prompt_step = PromptBuilder()
  prompt_output = prompt_step.invoke(
    PromptBuilderInput(
      question=request.question,
      stats=state.stats
    )
  )

  # 3. Run LLM
  llm_step = LLMRunner()
  llm_output = llm_step.invoke(prompt_output)

  # 4. Parse response
  parser_step = ResponseParser()
  parsed = parser_step.invoke(llm_output)

  # 5. Insert original question into final output
  parsed.question = request.question

  return parsed

@router.post("/ask")
def ask_ai(request: AskRequest):
    if state.stats is None:
        raise HTTPException(
            status_code=400,
            detail="No dataset uploaded. Upload data before asking questions."
        )

    return pipeline.run(request.question)