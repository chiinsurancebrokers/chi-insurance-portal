from pathlib import Path
import re

path = Path("run_local_portal.py")
s = path.read_text(encoding="utf-8")

start_pat = r"@app\.route\('/admin/renewals'\)\n@admin_required\ndef admin_renewals\(\):"
end_pat = r"\n@app\.route\('/admin/renewals/queue'"

m1 = re.search(start_pat, s)
m2 = re.search(end_pat, s)
if not (m1 and m2) or m2.start() <= m1.start():
    raise SystemExit("❌ Could not locate admin_renewals block safely.")

before = s[:m1.start()]
after = s[m2.start():]

replacement = """@app.route('/admin/renewals')
@admin_required
def admin_renewals():
    \"\"\"Show upcoming renewals (by expiry date) and queue emails.\"\"\"
    from datetime import timedelta
    db_session = get_session()

    try:
        today = datetime.now().date()
        days_ahead = request.args.get('days', 30, type=int)
        future_date = today + timedelta(days=days_ahead)

        # IMPORTANT: Renewals must be based on EXPIRY date (payment.expiry_date)
        rows = (
            db_session.query(Policy, Client, Payment)
            .join(Client, Policy.client_id == Client.id)
            .join(Payment, Payment.policy_id == Policy.id)
            .filter(Payment.expiry_date.isnot(None))
            .filter(Payment.expiry_date >= today)
            .filter(Payment.expiry_date <= future_date)
            .order_by(Payment.expiry_date.asc())
            .all()
        )

        renewal_list = []
        for policy, client, payment in rows:
            expiry = payment.expiry_date

            queued = db_session.query(EmailQueue).filter_by(
                policy_id=policy.id,
                payment_id=payment.id
            ).first()

            days_until = (expiry - today).days
            renewal_list.append({
                'client': client,
                'policy': policy,
                'payment': payment,
                'days_until': days_until,
                'queued': queued is not None,
                'sent': queued.status == EmailStatus.SENT if queued else False
            })

        return render_template('admin/renewals.html', renewals=renewal_list, days=days_ahead)

    finally:
        db_session.close()
"""

new_s = before + replacement + after
path.write_text(new_s, encoding="utf-8")
print("✅ Patched admin_renewals(): now uses Payment.expiry_date for upcoming renewals.")
