"""Hard-coded account profiles for synthetic data generation.

5 accounts covering the spec requirements:
- 3 deal outcomes (won, lost, stalled)
- 3+ persona types (analytical_evaluator, executive_champion, reluctant_adopter)
- 4 deal stages (discovery, evaluation, negotiation, close)
- 2 accounts with multi-call threads
"""

from __future__ import annotations

from dataclasses import dataclass, field

from customer_intelligence.schemas.transcript import (
    AccountProfile,
    StakeholderProfile,
)


@dataclass
class GenerationProfile:
    """Extended profile with generation instructions beyond what AccountProfile captures."""

    account: AccountProfile
    target_turn_count: int
    include_paralinguistic: bool
    objection_types: list[str]
    competitive_mentions: list[str]
    call_count: int = 1
    generation_notes: str = ""


PROFILES: list[GenerationProfile] = [
    # 1. TechCorp — mid-market, evaluation, Analytical Evaluator CFO → won
    GenerationProfile(
        account=AccountProfile(
            company_name="TechCorp",
            company_size="mid_market",
            industry="B2B SaaS",
            deal_stage="evaluation",
            deal_outcome="won",
            stakeholders=[
                StakeholderProfile(
                    name="David Chen",
                    role="CFO",
                    persona_type="analytical_evaluator",
                ),
                StakeholderProfile(
                    name="Sarah Kim",
                    role="VP Marketing",
                    persona_type="executive_champion",
                ),
            ],
        ),
        target_turn_count=35,
        include_paralinguistic=True,
        objection_types=["pricing", "implementation"],
        competitive_mentions=["CompetitorX"],
        generation_notes=(
            "CFO is the key decision-maker, asks detailed ROI questions. "
            "VP Marketing is the internal champion who brought the vendor in. "
            "Pricing objection is moderate — tied to company size, resolved with ROI argument. "
            "Implementation concern resolved with phased rollout proposal. "
            "Include text-audio divergence: CFO says pricing is 'reasonable' but with "
            "hesitation and low energy (hidden concern)."
        ),
    ),
    # 2. GrowthCo — startup, discovery, Executive Champion VP → won
    GenerationProfile(
        account=AccountProfile(
            company_name="GrowthCo",
            company_size="startup",
            industry="FinTech",
            deal_stage="discovery",
            deal_outcome="won",
            stakeholders=[
                StakeholderProfile(
                    name="Maria Rodriguez",
                    role="VP Growth",
                    persona_type="executive_champion",
                ),
            ],
        ),
        target_turn_count=20,
        include_paralinguistic=False,
        objection_types=["timeline"],
        competitive_mentions=[],
        generation_notes=(
            "Fast-moving startup. VP Growth is enthusiastic, strategic thinker. "
            "Focuses on outcomes not features. Short attention span for details. "
            "Wants to move fast — timeline concern is about speed of deployment, not risk. "
            "Strong buying signals throughout. No paralinguistic annotations."
        ),
    ),
    # 3. SafeGuard Inc — enterprise, negotiation, Reluctant Adopter CISO → stalled
    GenerationProfile(
        account=AccountProfile(
            company_name="SafeGuard Inc",
            company_size="enterprise",
            industry="Cybersecurity",
            deal_stage="negotiation",
            deal_outcome="stalled",
            stakeholders=[
                StakeholderProfile(
                    name="Robert Williams",
                    role="CISO",
                    persona_type="reluctant_adopter",
                ),
                StakeholderProfile(
                    name="Jennifer Park",
                    role="Head of Content",
                    persona_type="executive_champion",
                ),
            ],
        ),
        target_turn_count=45,
        include_paralinguistic=True,
        objection_types=["risk", "authority", "competition"],
        competitive_mentions=["CompetitorY", "CompetitorZ"],
        generation_notes=(
            "CISO is risk-averse, brought in by Head of Content but not bought in. "
            "Asks about security, compliance, data handling. Reluctant language throughout. "
            "Multiple competitors actively being evaluated. Authority objection: CISO "
            "defers to board for budget approval. Deal stalls because CISO can't get "
            "internal alignment. Include divergence: CISO says 'this looks promising' "
            "with flat tone, low energy, and crossed arms. Head of Content shows genuine "
            "enthusiasm but gets overruled."
        ),
    ),
    # 4. ScaleUp Ltd — SMB, evaluation→close, mixed personas → won (multi-call)
    GenerationProfile(
        account=AccountProfile(
            company_name="ScaleUp Ltd",
            company_size="smb",
            industry="E-commerce",
            deal_stage="close",
            deal_outcome="won",
            stakeholders=[
                StakeholderProfile(
                    name="Alex Turner",
                    role="CEO",
                    persona_type="executive_champion",
                ),
                StakeholderProfile(
                    name="Priya Sharma",
                    role="Marketing Director",
                    persona_type="analytical_evaluator",
                ),
            ],
        ),
        target_turn_count=25,
        include_paralinguistic=True,
        objection_types=["pricing", "need"],
        competitive_mentions=["CompetitorX"],
        call_count=2,
        generation_notes=(
            "Call 1 (evaluation): CEO is excited about the vision, Marketing Director "
            "wants to see the data. Pricing objection raised by Marketing Director. "
            "Call ends with 'let us think about it.' "
            "Call 2 (close): After receiving a case study, they re-engage. CEO drives "
            "the close, Marketing Director's concerns addressed. 'When can we start?' "
            "language. Include divergence in call 1: CEO's agreement feels genuine "
            "(high energy, leaning forward) while Marketing Director's agreement is "
            "lukewarm (neutral text, low energy)."
        ),
    ),
    # 5. Legacy Systems — enterprise, evaluation, multiple stakeholders → lost
    GenerationProfile(
        account=AccountProfile(
            company_name="Legacy Systems Corp",
            company_size="enterprise",
            industry="Manufacturing",
            deal_stage="evaluation",
            deal_outcome="lost",
            stakeholders=[
                StakeholderProfile(
                    name="Thomas Wright",
                    role="VP Operations",
                    persona_type="reluctant_adopter",
                ),
                StakeholderProfile(
                    name="Lisa Chang",
                    role="Digital Transformation Lead",
                    persona_type="analytical_evaluator",
                ),
                StakeholderProfile(
                    name="Mark Johnson",
                    role="CFO",
                    persona_type="reluctant_adopter",
                ),
            ],
        ),
        target_turn_count=50,
        include_paralinguistic=False,
        objection_types=["implementation", "risk", "need"],
        competitive_mentions=["CompetitorZ"],
        call_count=2,
        generation_notes=(
            "Call 1: Three stakeholders on the call. VP Ops is skeptical — doesn't see "
            "the need. Digital Transformation Lead is pushing for it but lacks authority. "
            "CFO is quiet, asks pointed budget questions. Deal feels stalled by end of call. "
            "Call 2: Follow-up after demo. VP Ops is even more resistant — 'we've done fine "
            "without this.' Digital Transformation Lead tries to make the case but gets "
            "shut down. Deal lost to status quo. No paralinguistic annotations."
        ),
    ),
]
