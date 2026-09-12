"""Curated semantic requirements shared by Stage 1.1 validators.

The capability codes are stable machine-readable identifiers. Human-readable
labels and asset mappings live in AGENT_COVERAGE.csv, but the required sets
below prevent a regenerated CSV from silently dropping a core capability.
"""

AGENT_REQUIRED_CAPABILITIES = {
    "A01": {"needs_discovery", "solution_design", "scope_baseline", "proposal_evidence", "bid_collaboration", "customer_risk"},
    "A02": {"project_initiation", "wbs_milestones", "resource_planning", "progress_control", "risk_control", "change_control", "meeting_coordination", "acceptance_closeout"},
    "A03": {"knowledge_governance", "knowledge_intake_review", "version_conflict_control", "knowledge_retirement", "knowledge_capture", "faq_retrieval", "cross_domain_retrieval"},
    "A04": {"meeting_planning", "minutes_generation", "decision_tracking", "action_followup", "project_coordination", "meeting_archiving"},
    "A05": {"business_writing", "solution_document", "meeting_document", "template_drafting", "evidence_based_drafting", "document_archiving"},
    "A06": {"document_format_rules", "format_inspection", "typesetting", "template_application", "format_repair", "positive_negative_examples"},
    "A07": {"workforce_request", "job_description", "candidate_screening", "interview_evaluation", "offer_onboarding", "privacy_compliance"},
    "A08": {"training_governance", "training_delivery", "competency_model", "performance_governance", "goal_setting", "midterm_review", "evaluation_feedback", "improvement_plan"},
    "A09": {"purchase_request", "sourcing_method", "supplier_admission", "supplier_comparison", "procurement_risk", "purchase_tracking"},
    "A10": {"tender_document_review", "bid_document_review", "qualification_review", "commercial_review", "technical_review", "scoring_review", "rejection_risk", "issue_traceability"},
    "A11": {"contract_review", "performance_tracking", "contract_change", "payment_control", "acceptance_control", "breach_risk", "ip_confidentiality", "evidence_traceability"},
    "A12": {"kpi_definition", "budget_analysis", "cost_analysis", "revenue_cash_analysis", "portfolio_analysis", "risk_change_analysis", "project_review", "management_reporting"},
}

SOURCE_AUTHORITIES = {"OFFICIAL", "PUBLIC_CORPORATE", "PUBLIC_CASE", "SYNTHETIC_DERIVED", "SYNTHETIC", "INTERNAL_DERIVED"}
SOURCE_TYPES = {"PUBLIC_OFFICIAL", "PUBLIC_CORPORATE", "PUBLIC_CASE", "SYNTHETIC_DERIVED", "SYNTHETIC", "INTERNAL_DERIVED"}
NORMATIVE_FORCES = {"MANDATORY", "CONTRACTUAL", "INTERNAL_MANDATORY", "GUIDANCE", "REFERENCE", "NONE"}
APPLICABILITIES = {"DIRECT", "CONDITIONAL", "ANALOGICAL", "NOT_APPLICABLE", "PENDING_REVIEW"}
