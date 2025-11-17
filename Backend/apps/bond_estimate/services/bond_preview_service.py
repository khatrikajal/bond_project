# apps/bond_estimate/services/bond_preview_service.py

def get_system_recommended(pbr):
    """Dummy system recommendations."""
    return {
        "recommended_issue_amount": 65000000,
        "recommended_coupon_rate": 7.80,
        "recommended_tenure": 4.5,
        "risk_score": "Low",
        "confidence_level": "High",
    }


def get_investment_metrics(pbr):
    """Dummy metrics."""
    projected_interest = float(pbr.issue_amount) * float(pbr.coupon_rate) / 100
    return {
        "total_subscription_target": float(pbr.issue_amount),
        
    }


def get_scenario_comparison(pbr):
    """Dummy scenario comparison block."""
    return {
        "parameters": [
            {
                "label": "Tenure (Years)",
                "your_input": float(pbr.tenure),
                "system_recommended": 4.5,
            },
            {
                "label": "Coupon Rate (%)",
                "your_input": float(pbr.coupon_rate),
                "system_recommended": 7.8,
            },
            {
                "label": "Preferred ROI (%)",
                "your_input": float(pbr.preferred_roi),
                "system_recommended": 7.75,
            },
            {
                "label": "Security Type",
                "your_input": pbr.security_type,
                "system_recommended": "Secured, Comfort",
            },
            {
                "label": "Total Estimated Cost",
                "your_input": "₹ 1,65,000",
                "system_recommended": "₹ 1,55,000",
            },
        ]
    }


def get_cost_breakdown():
    """Dummy cost breakdown chart."""
    chart = [
        {"label": "Professional and Advisory Fees", "value": 300000},
        {"label": "Regulatory and Statutory Costs", "value": 150000},
        {"label": "Placement and Distribution Costs", "value": 100000},
        {"label": "Documentation and Printing", "value": 250000},
        {"label": "Miscellaneous Costs", "value": 120000},
        {"label": "Security Creation and Compliance Costs", "value": 200000},
        {"label": "market and Communication", "value": 200000},
    ]

    total_cost = sum(item["value"] for item in chart)

    return {
        "chart": chart,
        "total_cost": total_cost,
    }


def build_preview_response(pbr):
    """Creates FINAL JSON structure for GET + PATCH output."""

    system_rec = get_system_recommended(pbr)

    return {
        "preliminary_bond_requirement": {
            "id": str(pbr.id),
            "company": str(pbr.company.company_id),
            "issue_amount": float(pbr.issue_amount),
            "tenure": float(pbr.tenure),
            "coupon_rate": float(pbr.coupon_rate),
        },

        "user_requirement_issue_amount": float(pbr.issue_amount),
        "system_recommended_issue_amount": system_rec["recommended_issue_amount"],

        "system_recommended": system_rec,
        "investment_metrics": get_investment_metrics(pbr),
        "scenario_comparison": get_scenario_comparison(pbr),
        "cost_breakdown": get_cost_breakdown(),
    }
