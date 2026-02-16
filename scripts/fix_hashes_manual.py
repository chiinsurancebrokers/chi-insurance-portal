with open('run_local_portal.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # After imports, before ADMIN definition
    if line.strip() == "from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus":
        new_lines.append("\n")
        new_lines.append("# Pre-computed password hashes\n")
        new_lines.append("ADMIN_HASH = 'pbkdf2:sha256:1000000$Q8loSbCXnQvZgCXz$ee8b167d28f37981fc8d18f8f7792c2bd4ffe4e620be3c0836b1e76d4967e651'\n")
        new_lines.append("DEMO_HASH = 'pbkdf2:sha256:1000000$8YEdUiTYWTuy44Ox$d1d9f17b11850a7a615fd449540662dda8c94133767ec3947b91c2eaa4590134'\n")
    
    # Replace ADMIN definition
    if "'password': generate_password_hash('CHIadmin2025!')" in line:
        new_lines[-1] = line.replace("generate_password_hash('CHIadmin2025!')", "ADMIN_HASH")
    
    # Replace all demo123
    if "'password': generate_password_hash('demo123')" in line:
        new_lines[-1] = line.replace("generate_password_hash('demo123')", "DEMO_HASH")

with open('run_local_portal.py', 'w') as f:
    f.writelines(new_lines)

print("✓ Fixed!")
