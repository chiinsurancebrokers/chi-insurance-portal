from src.database.models import get_session, Policy, Payment, PaymentStatus

def main():
    s = get_session()
    try:
        q = (
            s.query(Payment, Policy)
            .join(Policy, Policy.id == Payment.policy_id)
            .filter(
                Payment.status == PaymentStatus.PENDING,
                Policy.start_date.isnot(None),
            )
        )

        total = 0
        changed = 0

        for payment, policy in q.all():
            total += 1
            if payment.due_date != policy.start_date:
                payment.due_date = policy.start_date
                changed += 1

        s.commit()
        print(f"✅ Checked {total} pending payments. Updated due_date on {changed}.")
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

if __name__ == "__main__":
    main()
