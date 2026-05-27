from dataclasses import dataclass
from typing import Callable, List, Optional

from tools.base import ToolResult
from .workflows import WorkflowResult


REQUIRED_SLOTS = {"product_model", "symptom"}
OPTIONAL_SLOTS = {"observed_state", "attempted_steps"}


@dataclass(frozen=True)
class DiagnosisInput:
    product_model: str
    symptom: str
    observed_state: Optional[str] = None
    attempted_steps: Optional[List[str]] = None


class DiagnosisWorkflow:
    def __init__(self, knowledge_search: Callable[[str], ToolResult]):
        self.knowledge_search = knowledge_search

    def prepare(self, conversation_id: str, payload: dict) -> WorkflowResult:
        diagnosis_input = self._parse_input(payload)
        if diagnosis_input is None:
            return self._ask_user(
                "请提供产品型号和故障现象，以便为您排查问题。"
            )

        query = f"{diagnosis_input.product_model} {diagnosis_input.symptom}"
        result = self.knowledge_search(query)
        citations = result.citations

        if not citations:
            return WorkflowResult(
                response_type="handoff",
                content="当前知识库中未找到匹配的排障方案，已为您转接人工进一步确认。",
                metadata=self._metadata(diagnosis_input),
            )

        steps_content = self._build_steps(diagnosis_input, result.content)
        return WorkflowResult(
            response_type="final_answer",
            content=steps_content,
            citations=citations,
            metadata=self._metadata(diagnosis_input),
        )

    def _parse_input(self, payload: dict) -> Optional[DiagnosisInput]:
        if not isinstance(payload, dict):
            return None

        model = payload.get("product_model")
        symptom = payload.get("symptom")
        if not model or not isinstance(model, str) or not model.strip():
            return None
        if not symptom or not isinstance(symptom, str) or not symptom.strip():
            return None

        observed = payload.get("observed_state")
        if observed is not None and (not isinstance(observed, str) or not observed.strip()):
            return None

        steps = payload.get("attempted_steps")
        if steps is not None:
            if not isinstance(steps, list):
                return None
            steps = [s.strip() for s in steps if isinstance(s, str) and s.strip()]

        return DiagnosisInput(
            product_model=model.strip(),
            symptom=symptom.strip(),
            observed_state=observed.strip() if isinstance(observed, str) else None,
            attempted_steps=steps or None,
        )

    def _build_steps(self, diagnosis_input: DiagnosisInput, knowledge_content: str) -> str:
        parts = []
        parts.append(f"针对{diagnosis_input.product_model}「{diagnosis_input.symptom}」的问题，以下是排障建议：\n")
        parts.append(knowledge_content)

        if diagnosis_input.observed_state:
            parts.append(f"\n根据您描述的状态（{diagnosis_input.observed_state}），建议重点关注上述步骤。")
        if diagnosis_input.attempted_steps:
            tried = "、".join(diagnosis_input.attempted_steps)
            parts.append(f"\n您已尝试过：{tried}。如果以上步骤仍无法解决，建议联系售后或人工客服。")
        else:
            parts.append("\n如果以上步骤无法解决，建议联系售后或人工客服。")

        return "\n".join(parts)

    def _ask_user(self, content: str) -> WorkflowResult:
        return WorkflowResult(
            response_type="ask_user",
            content=content,
            metadata=self._metadata(None),
        )

    @staticmethod
    def _metadata(diagnosis_input: Optional[DiagnosisInput]) -> dict:
        meta = {"intent": "diagnosis", "workflow": "diagnosis"}
        if diagnosis_input:
            meta["product_model"] = diagnosis_input.product_model
            meta["symptom"] = diagnosis_input.symptom
        return meta
