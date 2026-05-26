"""
CHI Insurance AI Analyzer
Analyzes client needs and proposes insurance coverage gaps.
Integrated into HAL as render_chi_analyzer().
"""

# ── PROFESSION TRIGGERS ────────────────────────────────────────────────────────
PROFESSION_TRIGGERS = {
    "architect":         ["liability","home"],
    "engineer":          ["liability","home"],
    "civil engineer":    ["liability","home"],
    "doctor":            ["liability","health"],
    "lawyer":            ["liability"],
    "accountant":        ["liability"],
    "consultant":        ["liability"],
    "pharmacist":        ["liability"],
    "dentist":           ["liability","health"],
    "psychologist":      ["liability"],
    "real estate":       ["liability","home"],
    "business owner":    ["liability","life","health"],
    "self employed":     ["liability","health","life"],
    "teacher":           ["life","health"],
    "driver":            ["motor","life"],
    "pilot":             ["life","health"],
    "athlete":           ["health","life"],
    "expat":             ["health"],
    "freelancer":        ["liability","health"],
    "contractor":        ["liability","home"],
}

COVERAGE_MATRIX = {
    "motor":     {"label":"Motor Insurance",        "label_el":"Ασφάλεια Οχήματος",   "icon":"🚗", "priority":1},
    "health":    {"label":"Health Insurance",       "label_el":"Ασφάλεια Υγείας",     "icon":"❤️", "priority":1},
    "life":      {"label":"Life Insurance",         "label_el":"Ασφάλεια Ζωής",       "icon":"🫀", "priority":2},
    "home":      {"label":"Home / Property",        "label_el":"Ασφάλεια Κατοικίας",  "icon":"🏠", "priority":2},
    "liability": {"label":"Professional Liability", "label_el":"Επαγγελματική Ευθύνη","icon":"💼", "priority":1},
    "travel":    {"label":"Travel Insurance",       "label_el":"Ταξιδιωτική Ασφάλεια","icon":"✈️", "priority":3},
    "pet":       {"label":"Pet Insurance",          "label_el":"Ασφάλεια Κατοικίδιου","icon":"🐾", "priority":3},
    "income":    {"label":"Income Protection",      "label_el":"Ασφάλεια Εισοδήματος","icon":"💰", "priority":2},
    "critical":  {"label":"Critical Illness",       "label_el":"Κρίσιμες Παθήσεις",   "icon":"🏥", "priority":2},
    "education": {"label":"Education / Savings Plan","label_el":"Εκπαιδευτικό Πρόγραμμα","icon":"🎓","priority":3},
}

CARRIERS_PER_TYPE = {
    "motor":    ["3P Insurance","Hellas Direct","Groupama","Generali","Ethniki","AXA"],
    "health":   {"greek":["Groupama","Generali","Ethniki","Interamerican","Eurolife"],
                 "international":["Morgan Price","Bupa Global","NOW Health","Cigna"]},
    "life":     ["Generali","Ethniki","Interamerican","Eurolife","NN","Allianz"],
    "home":     ["Groupama","Generali","Ethniki","AXA","Interamerican"],
    "liability":["Groupama","Generali","Ethniki","AXA","Interamerican","Eurolife"],
    "travel":   ["Groupama","Generali","AXA","Allianz","Eurolife"],
    "pet":      ["Safe Pet System"],
    "income":   ["Generali","Ethniki","Interamerican","Eurolife"],
    "critical": ["Generali","Ethniki","Interamerican","NN"],
    "education":["Interamerican","Eurolife","NN","Allianz"],
}

def build_analyzer_prompt(client_data, existing_policies, lang="el"):
    """Build the Claude prompt for insurance needs analysis."""

    existing_types = [p.get("type","").lower() for p in existing_policies]
    profession = client_data.get("profession","").lower()
    age = client_data.get("age", "")
    family = client_data.get("family","")
    income = client_data.get("income","")
    assets = client_data.get("assets","")
    notes = client_data.get("notes","")
    is_expat = client_data.get("is_expat", False)
    has_property = client_data.get("has_property", False)
    has_pets = client_data.get("has_pets", False)
    has_children = client_data.get("has_children", False)
    has_vehicle = client_data.get("has_vehicle", False)
    travels_frequently = client_data.get("travels_frequently", False)

    existing_str = "\n".join(f"- {p.get('type','').title()}: {p.get('provider','')} {p.get('policy_no','')}" for p in existing_policies) if existing_policies else "No policies on file"

    carriers_info = """
Available carriers through Ashlar:
- Motor: 3P Insurance, Hellas Direct, Groupama, Generali, Ethniki, AXA
- Greek Health: Groupama, Generali, Ethniki, Interamerican, Eurolife
- International Health: Morgan Price (UK), Bupa Global (UK), NOW Health, Cigna
- Life: Generali, Ethniki, Interamerican, Eurolife, NN, Allianz
- Professional Liability: Groupama, Generali, Ethniki, AXA, Interamerican
- Home: Groupama, Generali, Ethniki, AXA, Interamerican
- Pet: Safe Pet System (via petshealth.gr)
- Travel: Groupama, Generali, AXA, Allianz

Key Greek market facts:
- Greek domestic health plans: NO free-network outpatient, NO dental, NO psychiatric outpatient, NO imaging outside hospitalisation
- International plans: full outpatient, diagnostics, dental (if selected), psychiatric, physio
- Professional Liability is LEGALLY REQUIRED for architects, engineers, doctors, lawyers in Greece
- Greek deductibles: per-hospitalisation OR annual (important to clarify)
- Expats/frequent travellers need international health (NOT Greek domestic)
"""

    if lang == "el":
        prompt = f"""Είσαι σύμβουλος ασφαλίσεων της Ashlar Insurance στην Ελλάδα. Ανάλυσε τις ασφαλιστικές ανάγκες αυτού του πελάτη και προτείνου ασφαλιστικά προγράμματα.

ΣΤΟΙΧΕΙΑ ΠΕΛΑΤΗ:
- Όνομα: {client_data.get('name','')}
- Ηλικία: {age}
- Επάγγελμα: {profession}
- Οικογένεια: {family}
- Εισόδημα: {income}
- Περιουσιακά στοιχεία: {assets}
- Έχει ακίνητο: {'Ναι' if has_property else 'Όχι'}
- Έχει όχημα: {'Ναι' if has_vehicle else 'Όχι'}
- Έχει κατοικίδιο: {'Ναι' if has_pets else 'Όχι'}
- Έχει παιδιά: {'Ναι' if has_children else 'Όχι'}
- Expat / Ταξιδεύει συχνά: {'Ναι' if (is_expat or travels_frequently) else 'Όχι'}
- Επιπλέον σημειώσεις: {notes}

ΥΠΑΡΧΟΥΣΕΣ ΑΣΦΑΛΙΣΕΙΣ:
{existing_str}

{carriers_info}

Δώσε δομημένη ανάλυση:

## 🔍 ΑΝΑΛΥΣΗ ΠΡΟΦΙΛ
Σύντομη εκτίμηση του ασφαλιστικού προφίλ (2-3 προτάσεις)

## ✅ ΚΑΛΥΨΕΙΣ ΠΟΥ ΕΧΕΙ
Τι έχει ήδη και αξιολόγηση

## ⚠️ ΚΕΝΑ ΚΑΛΥΨΕΩΝ
Για κάθε κενό:
- **[Είδος ασφάλισης]** — Επείγον 🔴 / Προτεινόμενο 🟡 / Προαιρετικό 🟢
- Γιατί το χρειάζεται (ειδικά για το επάγγελμα/προφίλ του)
- Προτεινόμενοι ασφαλιστές από το panel μας
- Εκτιμώμενο ετήσιο ασφάλιστρο (εύρος)

## 📋 ΠΛΑΝΟ ΔΡΑΣΗΣ
Προτεραιότητες (1-2-3) με χρονοδιάγραμμα

## 💬 SCRIPT ΕΠΙΚΟΙΝΩΝΙΑΣ
Ένα έτοιμο μήνυμα WhatsApp/email για να στείλεις στον πελάτη"""

    else:
        prompt = f"""You are an insurance adviser at Ashlar Insurance, Greece. Analyse this client's insurance needs and recommend coverage.

CLIENT PROFILE:
- Name: {client_data.get('name','')}
- Age: {age}
- Profession: {profession}
- Family: {family}
- Income: {income}
- Assets: {assets}
- Has property: {'Yes' if has_property else 'No'}
- Has vehicle: {'Yes' if has_vehicle else 'No'}
- Has pets: {'Yes' if has_pets else 'No'}
- Has children: {'Yes' if has_children else 'No'}
- Expat / Travels frequently: {'Yes' if (is_expat or travels_frequently) else 'No'}
- Notes: {notes}

EXISTING POLICIES:
{existing_str}

{carriers_info}

Provide structured analysis:

## 🔍 PROFILE ANALYSIS
Brief assessment of insurance profile (2-3 sentences)

## ✅ EXISTING COVERAGE
What they have and assessment

## ⚠️ COVERAGE GAPS
For each gap:
- **[Insurance type]** — Urgent 🔴 / Recommended 🟡 / Optional 🟢
- Why they need it (specific to their profession/profile)
- Recommended carriers from our panel
- Estimated annual premium (range)

## 📋 ACTION PLAN
Priorities (1-2-3) with timeline

## 💬 CLIENT SCRIPT
Ready WhatsApp/email message to send the client"""

    return prompt
