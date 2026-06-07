"""Unit tests for Codex decision tree evaluation logic."""

from tools.decision_tree import CodexAssessment, evaluate_codex_tree


def test_evaluate_codex_tree_ccp():
    """Verify that a step designed to eliminate/reduce a hazard resolves as a CCP."""
    assessment = CodexAssessment(
        hazard_name="Salmonella",
        process_step="Pasteurization",
        q1_has_control=True,
        q2_designed_to_prevent=True,
        q3_contamination_possible=True,
        q4_subsequent_step_prevents=False,
        reasoning="Step is pasteurization which is designed to eliminate pathogens."
    )
    is_ccp, path, reasoning = evaluate_codex_tree(assessment)
    assert is_ccp is True
    assert "Q1: Yes" in path[0]
    assert "Q2: Yes" in path[1]


def test_evaluate_codex_tree_not_ccp():
    """Verify that a step where subsequent steps mitigate the hazard resolves as NOT a CCP."""
    assessment = CodexAssessment(
        hazard_name="Salmonella",
        process_step="Raw milk reception",
        q1_has_control=True,
        q2_designed_to_prevent=False,
        q3_contamination_possible=True,
        q4_subsequent_step_prevents=True,
        reasoning="Subsequent pasteurization will eliminate the hazard."
    )
    is_ccp, path, reasoning = evaluate_codex_tree(assessment)
    assert is_ccp is False
    assert "Q4: Yes" in path[3]
