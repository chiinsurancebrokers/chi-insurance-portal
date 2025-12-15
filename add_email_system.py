with open('run_local_portal.py', 'r') as f:
    content = f.read()

# Add EmailQueue to imports
content = content.replace(
    'from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus',
    'from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus, EmailQueue, EmailStatus'
)

# Find insertion point (before if __name__)
lines = content.split('\n')
for i, line in enumerate(lines):
    if "if __name__ == '__main__':" in line:
        insert_pos = i
        break

# Email system routes
email_routes = '''
@app.route('/admin/renewals')
@admin_required
def admin_renewals():
    """Show upcoming renewals and queue emails"""
    from datetime import timedelta
    db_session = get_session()
    
    try:
        today = datetime.now().date()
        thirty_days = today + timedelta(days=30)
        
        policies = db_session.query(Policy).filter(
            Policy.expiration_date.between(today, thirty_days),
            Policy.status == PolicyStatus.ACTIVE
        ).order_by(Policy.expiration_date).all()
        
        renewal_list = []
        for policy in policies:
            try:
                client = policy.client
                if not client:
                    continue
                
                payment = db_session.query(Payment).filter_by(
                    policy_id=policy.id,
                    status=PaymentStatus.PENDING
                ).first()
                
                if payment:
                    days_until = (policy.expiration_date - today).days
                    
                    # Check if already queued
                    queued = db_session.query(EmailQueue).filter_by(
                        policy_id=policy.id,
                        payment_id=payment.id
                    ).first()
                    
                    renewal_list.append({
                        'client': client,
                        'policy': policy,
                        'payment': payment,
                        'days_until': days_until,
                        'queued': queued is not None,
                        'sent': queued.status == EmailStatus.SENT if queued else False
                    })
            except Exception:
                continue
        
        return render_template('admin/renewals.html', renewals=renewal_list)
    finally:
        db_session.close()

@app.route('/admin/renewals/queue', methods=['POST'])
@admin_required
def admin_queue_emails():
    """Queue selected emails"""
    selected_ids = request.form.getlist('selected')
    
    if not selected_ids:
        flash('No emails selected', 'warning')
        return redirect(url_for('admin_renewals'))
    
    db_session = get_session()
    queued_count = 0
    
    try:
        for policy_id in selected_ids:
            policy = db_session.query(Policy).get(int(policy_id))
            if not policy:
                continue
            
            client = policy.client
            payment = db_session.query(Payment).filter_by(
                policy_id=policy.id,
                status=PaymentStatus.PENDING
            ).first()
            
            if not client or not client.email or not payment:
                continue
            
            # Check if already queued
            existing = db_session.query(EmailQueue).filter_by(
                policy_id=policy.id,
                payment_id=payment.id
            ).first()
            
            if existing:
                continue
            
            # Generate email content
            has_greek = any(ord(char) > 127 for char in client.name)
            language = 'el' if has_greek else 'en'
            days_until = (payment.due_date - datetime.now().date()).days
            
            subject, body = generate_renewal_email(client, policy, payment, days_until, language)
            
            # Queue email
            email = EmailQueue(
                client_id=client.id,
                policy_id=policy.id,
                payment_id=payment.id,
                recipient_email=client.email,
                subject=subject,
                body_html=body,
                status=EmailStatus.QUEUED
            )
            
            db_session.add(email)
            queued_count += 1
        
        db_session.commit()
        flash(f'Queued {queued_count} emails', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        db_session.close()
    
    return redirect(url_for('admin_email_queue'))

@app.route('/admin/email-queue')
@admin_required
def admin_email_queue():
    """Show email queue"""
    db_session = get_session()
    
    try:
        emails = db_session.query(EmailQueue).order_by(EmailQueue.created_date.desc()).all()
        
        email_list = []
        for email in emails:
            email_list.append({
                'id': email.id,
                'client_name': email.client.name,
                'recipient': email.recipient_email,
                'subject': email.subject,
                'status': email.status.value,
                'sent_at': email.sent_at,
                'error': email.error_message,
                'created': email.created_date
            })
        
        return render_template('admin/email_queue.html', emails=email_list)
    finally:
        db_session.close()

@app.route('/admin/email/send/<int:email_id>', methods=['POST'])
@admin_required
def admin_send_email(email_id):
    """Send a single queued email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', 'xiatropoulos@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    if not SMTP_PASSWORD:
        flash('Email not configured', 'danger')
        return redirect(url_for('admin_email_queue'))
    
    db_session = get_session()
    
    try:
        email = db_session.query(EmailQueue).get(email_id)
        if not email:
            flash('Email not found', 'danger')
            return redirect(url_for('admin_email_queue'))
        
        # Send email
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USER
        msg['To'] = email.recipient_email
        msg['Subject'] = email.subject
        msg.attach(MIMEText(email.body_html, 'html', 'utf-8'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        # Update status
        email.status = EmailStatus.SENT
        email.sent_at = datetime.now()
        db_session.commit()
        
        flash(f'Email sent to {email.recipient_email}', 'success')
    except Exception as e:
        email.status = EmailStatus.FAILED
        email.error_message = str(e)
        db_session.commit()
        flash(f'Failed: {str(e)}', 'danger')
    finally:
        db_session.close()
    
    return redirect(url_for('admin_email_queue'))

def generate_renewal_email(client, policy, payment, days_until, language):
    """Generate email subject and body"""
    if language == 'el':
        subject = f"Ανανέωση Ασφαλιστηρίου - {policy.policy_type}"
        body = f"""<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #d32f2f;">Υπενθύμιση Ανανέωσης Ασφαλιστηρίου</h2>
    <p>Αγαπητή/έ <strong>{client.name}</strong>,</p>
    <p>Σας ενημερώνουμε ότι το ασφαλιστήριό σας πλησιάζει στη λήξη του.</p>
    <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
        <strong>Υπολείπονται {days_until} {'ημέρα' if days_until == 1 else 'ημέρες'} μέχρι τη λήξη</strong>
    </div>
    <h3 style="color: #1976d2;">Στοιχεία Ασφαλιστηρίου</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Είδος:</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{policy.policy_type}</td>
        </tr>
        {'<tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Πινακίδα:</strong></td><td style="padding: 10px; border: 1px solid #ddd;">' + policy.license_plate + '</td></tr>' if policy.license_plate else ''}
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Ασφάλιστρο:</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">€{payment.amount:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Ημερομηνία Λήξης:</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{payment.due_date.strftime('%d/%m/%Y')}</td>
        </tr>
    </table>
    <p style="margin-top: 30px;">Με εκτίμηση,<br><strong>CHI Insurance Brokers</strong></p>
</div></body></html>"""
    else:
        subject = f"Insurance Renewal - {policy.policy_type}"
        body = f"""<html><body style="font-family: Arial, sans-serif;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2>Insurance Renewal Reminder</h2>
    <p>Dear <strong>{client.name}</strong>,</p>
    <p>Your insurance policy is approaching expiration.</p>
    <p><strong>{days_until} days remaining</strong></p>
    <p><strong>Amount:</strong> €{payment.amount:.2f}<br>
    <strong>Expires:</strong> {payment.due_date.strftime('%d/%m/%Y')}</p>
    <p>Best regards,<br><strong>CHI Insurance Brokers</strong></p>
</div></body></html>"""
    
    return subject, body

'''

lines.insert(insert_pos, email_routes)
content = '\n'.join(lines)

with open('run_local_portal.py', 'w') as f:
    f.write(content)

print("✓ Added email system routes")
