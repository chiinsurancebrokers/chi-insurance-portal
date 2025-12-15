with open('run_local_portal.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_function = False
skip_count = 0

for i, line in enumerate(lines):
    # Skip email-related functions
    if '@app.route(\'/admin/renewals' in line:
        skip_function = True
        skip_count = 0
        continue
    
    if skip_function:
        skip_count += 1
        # Skip until we hit another @app.route or if __name__
        if ('@app.route' in line and '/admin/renewals' not in line) or 'if __name__' in line:
            skip_function = False
            new_lines.append(line)
        continue
    
    # Skip generate_email_body function
    if 'def generate_email_body' in line:
        skip_function = True
        continue
    
    new_lines.append(line)

with open('run_local_portal.py', 'w') as f:
    f.writelines(new_lines)

print("Removed email routes")
