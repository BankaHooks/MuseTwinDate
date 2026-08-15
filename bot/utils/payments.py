from datetime import datetime, timedelta

PLANS = {
    "1": {"months": 1, "price": 100, "label": "1 month"},
    "3": {"months": 3, "price": 250, "label": "3 months"},
}

def create_invoice_payload(plan_key: str, user_id: int) -> str:
    return f"premium_{plan_key}_{user_id}_{datetime.utcnow().timestamp()}"

def get_premium_expiry(duration_months: int) -> datetime:
    return datetime.utcnow() + timedelta(days=30*duration_months)