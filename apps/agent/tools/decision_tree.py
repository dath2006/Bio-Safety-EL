"""Codex 2020 CCP Decision Tree evaluation tool."""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class CodexAssessment(BaseModel):
    """Pydantic model representing Codex Decision Tree answers for a hazard."""

    hazard_name: str = Field(description="Name of the hazard")
    process_step: str = Field(description="Process step where the hazard occurs")
    q1_has_control: bool = Field(
        description="Q1: Do control measures exist at this step or subsequent steps for the hazard?"
    )
    q1_sub_necessary: Optional[bool] = Field(
        default=None,
        description="If Q1 is No: Is control at this step necessary for safety? (True/False/None)"
    )
    q2_designed_to_prevent: bool = Field(
        description="Q2: Is the step specifically designed to eliminate or reduce the likely occurrence of a hazard to an acceptable level?"
    )
    q3_contamination_possible: bool = Field(
        description="Q3: Could contamination with the hazard occur in excess of acceptable levels or increase to unacceptable levels?"
    )
    q4_subsequent_step_prevents: bool = Field(
        description="Q4: Will a subsequent step eliminate the hazard or reduce its likely occurrence to an acceptable level?"
    )
    reasoning: str = Field(description="Deductive explanation for the answers to the questions")


def evaluate_codex_tree(assessment: CodexAssessment) -> Tuple[bool, List[str], str]:
    """
    Evaluate Codex 2020 decision tree logic from answers.
    Returns: (is_ccp, decision_tree_path, reasoning)
    """
    path = []
    
    # Q1: Control measures exist?
    if not assessment.q1_has_control:
        path.append("Q1: No (No control measures exist)")
        if assessment.q1_sub_necessary:
            path.append("Q1 Sub: Yes (Control at this step is necessary for safety -> Modify step/process)")
            reasoning = (
                f"No control measures exist for {assessment.hazard_name} at step '{assessment.process_step}', "
                f"but control is necessary for safety. The step or process must be modified to include a control, making it a CCP."
            )
            return True, path, reasoning
        else:
            path.append("Q1 Sub: No (Control at this step is not necessary for safety)")
            reasoning = (
                f"No control measures exist for {assessment.hazard_name} at step '{assessment.process_step}', "
                f"and control at this step is not necessary for safety. Not a CCP."
            )
            return False, path, reasoning
    
    path.append("Q1: Yes (Control measures exist)")
    
    # Q2: Specifically designed?
    if assessment.q2_designed_to_prevent:
        path.append("Q2: Yes (Step specifically designed to control hazard)")
        reasoning = (
            f"Step '{assessment.process_step}' is specifically designed to eliminate/reduce "
            f"{assessment.hazard_name} to acceptable levels. This step is a CCP."
        )
        return True, path, reasoning
    
    path.append("Q2: No (Step not specifically designed to control hazard)")
    
    # Q3: Contamination possible?
    if not assessment.q3_contamination_possible:
        path.append("Q3: No (Contamination/increase beyond limits unlikely)")
        reasoning = (
            f"Contamination with {assessment.hazard_name} or increase to unacceptable levels is unlikely "
            f"to occur at step '{assessment.process_step}'. Not a CCP."
        )
        return False, path, reasoning
    
    path.append("Q3: Yes (Contamination/increase beyond limits is possible)")
    
    # Q4: Subsequent step prevents?
    if assessment.q4_subsequent_step_prevents:
        path.append("Q4: Yes (Subsequent step will control hazard)")
        reasoning = (
            f"A subsequent process step will eliminate or reduce {assessment.hazard_name} "
            f"to acceptable levels. This step is not a CCP; the subsequent step should be the CCP."
        )
        return False, path, reasoning
    
    path.append("Q4: No (No subsequent step will control hazard)")
    reasoning = (
        f"Contamination could occur or increase at step '{assessment.process_step}', and no subsequent step "
        f"will eliminate or reduce {assessment.hazard_name}. Therefore, this step must be a CCP."
    )
    return True, path, reasoning
