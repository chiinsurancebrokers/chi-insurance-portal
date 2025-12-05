# CHI Insurance Portal - Command Reference

## Quick Start
```bash
cd ~/Documents/CHI_Insurance_Portal
source venv/bin/activate
```

---

## Dashboard & Reporting

**View payment dashboard**
```bash
python manage.py status
```
Shows: Total policies, active/inactive, paid/pending/overdue payments, upcoming due dates

---

## Client Management

**List all clients**
```bash
python manage.py clients
```

**Search for a client**
```bash
python manage.py search ΜΑΜΜΗ
python manage.py search ΑΛΕΞΟΠΟΥΛΟΣ
```

**Edit client information**
```bash
python manage.py edit 4
```
Prompts for: Name, Email, Phone, Address  
Leave blank to keep current value, type 'null' to clear

---

## Payment Tracking

**List pending payments**
```bash
python manage.py pending
```

**List paid payments**
```bash
python manage.py paid
```

**Mark payment as PAID**
```bash
python manage.py mark-paid 1919634
```
Requires policy number

**Mark payment as UNPAID (reverse)**
```bash
python manage.py mark-unpaid 1919634
```

---

## Policy Management

**Add new policy interactively**
```bash
python manage.py add-policy
```
Prompts for:
- Client name (existing or new)
- Email, phone, address (optional)
- Policy number (optional)
- Provider (e.g., HELLAS DIRECT, GENERALI)
- Policy type (ΑΥΤΟΚΙΝΗΤΟ, ΖΩΗΣ, ΠΥΡΟΣ, OTHER)
- License plate (for auto insurance)
- Premium amount
- Due date (DD/MM/YYYY format)
- Payment code/RF code (optional)

---

## PDF Processing & OCR

**Extract data from single PDF**
```bash
python src/ocr/pdf_extractor.py data/raw_pdfs/paymentnotice.pdf
```

**Batch extract from all PDFs in folder**
```bash
python src/ocr/pdf_extractor.py data/raw_pdfs/
```
Supported formats:
- 3P Insurance (full extraction)
- Hellas Direct (payment info)
- ATLANTIKI, GENERALI (auto-detected)

**Import extracted data to database**
```bash
python src/database/import_data.py
```
Imports from: data/processed/extracted_data.csv

---

## File Structure

**Where to put new PDFs**
```
data/raw_pdfs/
```

**Where extracted data is saved**
```
data/processed/extracted_data.csv
```

**Database location**
```
data/database/chi_insurance.db
```

**Archived PDFs from sent emails**
```
../renewal_system_v2/sent_pdfs/
```

---

## Monthly Workflow

### Step 1: Upload PDFs
Place all new PDFs in `data/raw_pdfs/`

### Step 2: Extract Data
```bash
python src/ocr/pdf_extractor.py data/raw_pdfs/
```
Review output - shows format detection and extracted info

### Step 3: Import to Database
```bash
python src/database/import_data.py
```
Imports clients, policies, and creates pending payments

### Step 4: Handle Manual Entries
For any skipped/unknown format PDFs:
```bash
python manage.py add-policy
```

### Step 5: Review Status
```bash
python manage.py status
python manage.py pending
```

### Step 6: Track Payments
As payments come in:
```bash
python manage.py mark-paid <policy_number>
```

---

## Common Workflows

**Check who needs to pay**
```bash
python manage.py status
python manage.py pending
```

**Client called and paid**
```bash
python manage.py search <name>
python manage.py mark-paid <policy_number>
python manage.py status
```

**Fix client typo**
```bash
python manage.py search <name>
python manage.py edit <client_id>
```

**Add missing policy from PDF**
```bash
python manage.py add-policy
```

---

## Troubleshooting

**Module not found error**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Database doesn't exist**
```bash
python src/database/import_data.py
```

**No data in CSV to import**
```bash
python src/ocr/pdf_extractor.py data/raw_pdfs/
```

**Greek characters showing as boxes**
Ensure DejaVu fonts are installed:
```bash
ls fonts/DejaVuSans.ttf
```

---

## Integration with Renewal System

The renewal system is located at:
```
../renewal_system_v2/
```

**Send renewal emails (with PDFs)**
```bash
cd ../renewal_system_v2
python renewal_invitations_bilingual.py
```

**Dry run (test without sending)**
```bash
cd ../renewal_system_v2
python renewal_invitations_bilingual.py --dry-run
```

---

## Technical Details

**Database**: SQLite 3  
**Tables**: clients, policies, payments, documents  
**Python**: 3.9+  
**OCR Library**: pdfplumber  
**Supported Languages**: Greek (with accents), English

---

## Getting Help

**Show all available commands**
```bash
python manage.py
```

**View this file**
```bash
cat COMMANDS.md
```

**Start with banner**
```bash
./start.sh
```

---

*Last updated: December 2025*
