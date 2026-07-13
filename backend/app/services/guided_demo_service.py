from app.models.domain import GuidedDemo


GUIDED_DEMOS = [
    GuidedDemo(
        id="healthy-approval",
        title="Healthy borrower approval",
        borrower_id="vantage-services",
        route="/analysis/vantage-services",
        explanation="Review an asset-light services borrower with strong cash generation and manageable leverage.",
        learning_point="See how consolidated leverage, coverage, liquidity, and covenant headroom support an approval.",
        talking_points=[
            "Open the metric explanations to trace formulas and source periods.",
            "Compare base and mild downside covenant survival.",
            "Use the audit trail to distinguish supportive rules from adverse rules.",
        ],
        expected_outcome="Approve in the default structure, with no base or mild quarterly breach.",
    ),
    GuidedDemo(
        id="distressed-decline",
        title="Distressed borrower decline",
        borrower_id="ironbridge-components",
        route="/analysis/ironbridge-components",
        explanation="Inspect a highly leveraged manufacturer with falling revenue, compressed margins, and weak liquidity.",
        learning_point="See the first quarterly breach and the exact covenant evidence that drives a decline.",
        talking_points=[
            "Start with the first-breach timeline.",
            "Open Why this recommendation? and inspect PC-DECLINE-01.",
            "Move to sensitivity to see how additional stress worsens leverage and coverage.",
        ],
        expected_outcome="Decline, with a clearly cited FY2026 quarterly covenant breach.",
    ),
    GuidedDemo(
        id="structure-comparison",
        title="Conservative versus aggressive structure",
        route="/analyses",
        explanation="Save two cases for the same borrower, then compare a lower-debt, higher-equity structure with an aggressive structure.",
        learning_point="See how a deterministic safety score ranks structures using leverage, coverage, liquidity, equity, and covenant survival.",
        talking_points=[
            "Duplicate the borrower case with modified debt and sponsor equity.",
            "Select both saved rows and run the backend comparison.",
            "Review the safer-structure rationale and score components.",
        ],
        expected_outcome="The lower-leverage or higher-equity structure is identified as safer.",
    ),
]


def get_guided_demos() -> list[GuidedDemo]:
    return GUIDED_DEMOS
