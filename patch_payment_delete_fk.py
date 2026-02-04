from pathlib import Path

path = Path("run_local_portal.py")
lines = path.read_text(encoding="utf-8").splitlines()

out = []
inside = False

for i, line in enumerate(lines):
    # detect start of the function
    if line.strip() == "@app.route('/admin/payment/<int:payment_id>/delete', methods=['POST'])":
        inside = True
        out.append(line)
        continue

    if inside and line.strip() == "@admin_required":
        out.append(line)
        out.append("def admin_delete_payment(payment_id):")
        out.append("    db_session = get_session()")
        out.append("    try:")
        out.append("        # Clear dependent email_queue rows first (FK constraint)")
        out.append("        db_session.query(EmailQueue).filter_by(payment_id=payment_id).delete(synchronize_session='fetch')")
        out.append("")
        out.append("        payment = db_session.query(Payment).get(payment_id)")
        out.append("        if not payment:")
        out.append("            flash('Payment not found', 'danger')")
        out.append("            db_session.commit()")
        out.append("            return redirect(url_for('admin_payments'))")
        out.append("")
        out.append("        db_session.delete(payment)")
        out.append("        db_session.commit()")
        out.append("        flash('Payment deleted successfully!', 'success')")
        out.append("        return redirect(url_for('admin_payments'))")
        out.append("")
        out.append("    except Exception as e:")
        out.append("        db_session.rollback()")
        out.append("        flash(f'Delete failed: {type(e).__name__}', 'danger')")
        out.append("        return redirect(url_for('admin_payments'))")
        out.append("")
        out.append("    finally:")
        out.append("        db_session.close()")
        continue

    # skip old function body until redirect line
    if inside:
        if "return redirect(url_for('admin_payments'))" in line:
            inside = False
        continue

    out.append(line)

path.write_text("\n".join(out) + "\n", encoding="utf-8")
print("✅ admin_delete_payment safely patched.")
