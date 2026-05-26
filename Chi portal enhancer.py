"""
CHI Portal Enhancements — Railway-side additions
Add to chi-insurance-portal repo alongside app.py
Handles: multi-insurer CSV parsing, commissions, renewal risk scoring,
         automated renewal messages, REST API routes, portfolio summaries
"""
import csv, io, re
from datetime import datetime, date, timedelta

# ══════════════════════════════════════════════════════════════════════════════
# 1. MULTI-INSURER CSV PARSERS
# ══════════════════════════════════════════════════════════════════════════════

def parse_csv_auto(file_content: str) -> tuple[str, list[dict]]:
    """Auto-detect insurer format and parse. Returns (insurer_name, [policy_dicts])."""
    sample = file_content[:500].lower()

    if "ar. kyklof" in sample or "αρ. κυκλ" in sample or "ονοματεπώνυμο" in sample.lower():
        return "Hellas Direct", parse_hellas_direct(file_content)
    if "license plate" in sample or "insurance type" in sample:
        return "3P Insurance", parse_3p(file_content)
    if "policy number" in sample and "morgan" in sample:
        return "Morgan Price", parse_morgan_price(file_content)
    if "member id" in sample or "bupa" in sample:
        return "Bupa Global", parse_bupa(file_content)
    if "policy no" in sample and ("groupama" in sample or "γκρουπαμα" in sample):
        return "Groupama", parse_groupama(file_content)
    if "generali" in sample or "ασφαλιστ" in sample:
        return "Generic Greek", parse_generic_greek(file_content)
    return "Unknown", parse_generic_greek(file_content)

def _csv_rows(content: str, delimiter=";"):
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    return list(reader)

def _parse_date(d: str) -> str:
    """Parse various date formats to ISO."""
    if not d: return ""
    for fmt in ["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%m/%d/%Y","%d.%m.%Y"]:
        try: return datetime.strptime(d.strip(), fmt).date().isoformat()
        except: pass
    return d.strip()

def _normalize(row: dict, mapping: dict) -> dict:
    """Apply field mapping to normalize a row."""
    result = {}
    for target, sources in mapping.items():
        for src in (sources if isinstance(sources, list) else [sources]):
            val = row.get(src, row.get(src.lower(), "")).strip()
            if val:
                result[target] = val
                break
    return result

def parse_3p(content: str) -> list[dict]:
    mapping = {
        "client_name":   ["CLIENT NAME","Client Name"],
        "policy_type":   ["INSURANCE TYPE","Insurance Type"],
        "insurer":       ["INSURANCE COMPANY","Insurance Company"],
        "vehicle_plate": ["LICENSE PLATE","License Plate"],
        "premium":       ["PREMIUM AMOUNT","Premium Amount","PREMIUM"],
        "expiry_date":   ["EXPIRY DATE","Expiry Date","EXPIRY"],
    }
    rows = _csv_rows(content)
    results = []
    for row in rows:
        p = _normalize(row, mapping)
        if p.get("client_name"):
            p["expiry_date"] = _parse_date(p.get("expiry_date",""))
            p["source"] = "3P Insurance"
            p["policy_category"] = "motor"
            results.append(p)
    return results

def parse_hellas_direct(content: str) -> list[dict]:
    mapping = {
        "client_name":   ["Ονοματεπώνυμο","ΟΝΟΜΑΤΕΠΩΝΥΜΟ","Name"],
        "vehicle_plate": ["Αρ. Κυκλοφορίας","ΑΡ. ΚΥΚΛΟΦΟΡΙΑΣ","Plate"],
        "premium":       ["Ασφάλιστρο","ΑΣΦΑΛΙΣΤΡΟ","Premium"],
        "expiry_date":   ["Λήξη","ΛΗΞΗ","Expiry"],
        "policy_number": ["Αρ. Ασφαλιστηρίου","Policy No"],
    }
    rows = _csv_rows(content)
    results = []
    for row in rows:
        p = _normalize(row, mapping)
        if p.get("client_name"):
            p["expiry_date"] = _parse_date(p.get("expiry_date",""))
            p["source"] = "Hellas Direct"
            p["policy_category"] = "motor"
            results.append(p)
    return results

def parse_morgan_price(content: str) -> list[dict]:
    mapping = {
        "client_name":  ["Name","CLIENT NAME","Member Name"],
        "policy_number":["Policy Number","POLICY NUMBER","Policy No"],
        "product":      ["Product","PRODUCT","Plan"],
        "premium":      ["Premium","PREMIUM","Annual Premium"],
        "currency":     ["Currency","CURRENCY","CCY"],
        "expiry_date":  ["Expiry","EXPIRY","Renewal Date","Expiry Date"],
        "dob":          ["DOB","Date of Birth","D.O.B"],
    }
    rows = _csv_rows(content, delimiter=",")
    results = []
    for row in rows:
        p = _normalize(row, mapping)
        if p.get("client_name"):
            p["expiry_date"] = _parse_date(p.get("expiry_date",""))
            p["source"] = "Morgan Price"
            p["policy_category"] = "health"
            p["insurer"] = "Morgan Price"
            results.append(p)
    return results

def parse_bupa(content: str) -> list[dict]:
    mapping = {
        "client_name":  ["Member Name","Name","MEMBER NAME"],
        "policy_number":["Policy Number","POLICY NUMBER","Membership No"],
        "product":      ["Product","Plan","PRODUCT"],
        "premium":      ["Premium","Annual Premium"],
        "currency":     ["Currency","CCY"],
        "expiry_date":  ["Renewal Date","Expiry Date","End Date"],
    }
    rows = _csv_rows(content, delimiter=",")
    results = []
    for row in rows:
        p = _normalize(row, mapping)
        if p.get("client_name"):
            p["expiry_date"] = _parse_date(p.get("expiry_date",""))
            p["source"] = "Bupa Global"
            p["policy_category"] = "health"
            p["insurer"] = "Bupa Global"
            results.append(p)
    return results

def parse_groupama(content: str) -> list[dict]:
    mapping = {
        "client_name":  ["Ονοματεπώνυμο","Ασφαλισμένος","Name"],
        "policy_number":["Αρ. Συμβολαίου","Policy No","Αριθμός"],
        "product":      ["Προϊόν","Product","Πρόγραμμα"],
        "premium":      ["Ασφάλιστρο","Premium"],
        "expiry_date":  ["Λήξη","Expiry","Ημ/νία Λήξης"],
    }
    rows = _csv_rows(content)
    results = []
    for row in rows:
        p = _normalize(row, mapping)
        if p.get("client_name"):
            p["expiry_date"] = _parse_date(p.get("expiry_date",""))
            p["source"] = "Groupama"
            results.append(p)
    return results

def parse_generic_greek(content: str) -> list[dict]:
    """Fallback parser for any Greek insurer CSV."""
    delimiter = ";" if content.count(";") > content.count(",") else ","
    rows = _csv_rows(content, delimiter=delimiter)
    if not rows: return []
    # Auto-map first row keys heuristically
    results = []
    for row in rows:
        keys = list(row.keys())
        p = {"raw": row}
        for k, v in row.items():
            kl = k.lower()
            if any(x in kl for x in ["name","ονομ","ασφαλισ"]): p["client_name"] = v
            elif any(x in kl for x in ["policy","συμβόλ","ασφαλιστ","αρ."]): p["policy_number"] = v
            elif any(x in kl for x in ["premium","ασφάλιστρ","ποσό"]): p["premium"] = v
            elif any(x in kl for x in ["expir","λήξ","ημ/νία"]): p["expiry_date"] = _parse_date(v)
            elif any(x in kl for x in ["plate","κυκλ","πινακ"]): p["vehicle_plate"] = v
        if p.get("client_name"): results.append(p)
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 2. RENEWAL RISK SCORING
# ══════════════════════════════════════════════════════════════════════════════

def renewal_risk_score(policy: dict, payment_history: list = None) -> dict:
    """
    Score renewal risk for a policy. Returns:
    {score: 0-100, level: 'safe'|'watch'|'at_risk', factors: [...], badge: str}
    """
    score = 50  # neutral start
    factors = []

    # Factor 1: Days until expiry
    expiry = policy.get("expiry_date","")
    days = None
    if expiry:
        try:
            d = date.fromisoformat(expiry)
            days = (d - date.today()).days
        except: pass

    if days is not None:
        if days < 0:
            score -= 30; factors.append("🔴 Expired")
        elif days <= 14:
            score -= 20; factors.append("🔴 Expiring in 14 days")
        elif days <= 30:
            score -= 10; factors.append("🟡 Expiring in 30 days")
        elif days > 90:
            score += 10; factors.append("🟢 >90 days to renewal")

    # Factor 2: Payment history
    if payment_history:
        overdue = sum(1 for p in payment_history if "overdue" in str(p.get("status","")).lower())
        if overdue > 2:
            score -= 25; factors.append(f"🔴 {overdue} overdue payments")
        elif overdue == 1:
            score -= 10; factors.append("🟡 1 overdue payment")
        else:
            score += 10; factors.append("🟢 Clean payment history")

    # Factor 3: Premium amount (proxy for client value)
    try:
        prem = float(str(policy.get("premium","0")).replace(",","").replace("€","").replace("£","").strip() or 0)
        if prem > 2000: score += 10; factors.append("💰 High premium client")
    except: pass

    # Clamp
    score = max(0, min(100, score))

    if score >= 65:   level, badge = "safe",    "🟢 Safe"
    elif score >= 40: level, badge = "watch",   "🟡 Watch"
    else:             level, badge = "at_risk", "🔴 At Risk"

    return {"score": score, "level": level, "badge": badge, "factors": factors, "days": days}


# ══════════════════════════════════════════════════════════════════════════════
# 3. RENEWAL MESSAGE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def renewal_message_email(policy: dict, portal_url: str = "", lang: str = "el") -> str:
    """Generate personalised bilingual renewal email body."""
    name   = policy.get("client_name","Αγαπητέ πελάτη")
    ptype  = policy.get("policy_category","ασφάλεια")
    prov   = policy.get("insurer","")
    pno    = policy.get("policy_number","")
    prem   = policy.get("premium","")
    expiry = policy.get("expiry_date","")
    plate  = policy.get("vehicle_plate","")

    expiry_display = expiry.replace("-","/") if expiry else "—"
    portal_line = f"\n🔗 Προσωπικό portal: {portal_url}" if portal_url else ""

    if lang == "el":
        return f"""Αγαπητέ/ή {name},

Σας ενημερώνουμε ότι η ασφάλεια {ptype} {"(" + prov + ")" if prov else ""} {"αρ. " + pno if pno else ""} {"για το όχημα " + plate if plate else ""} λήγει στις {expiry_display}.

💰 Ετήσιο ασφάλιστρο: {prem} {"€" if prem and "€" not in prem and "£" not in prem else ""}

Για να ανανεώσετε την ασφάλειά σας, επικοινωνήστε μαζί μας:
📞 +30 210 0000000
✉️ info@chiinsurancebrokers.com
💬 WhatsApp: +30 210 0000000{portal_line}

Με εκτίμηση,
Χρήστος Ιατρόπουλος
Ashlar Insurance"""
    else:
        return f"""Dear {name},

We would like to inform you that your {ptype} insurance {"(" + prov + ")" if prov else ""} {"policy no. " + pno if pno else ""} {"for vehicle " + plate if plate else ""} expires on {expiry_display}.

💰 Annual premium: {prem}

To renew your policy, please contact us:
📞 +30 210 0000000
✉️ info@chiinsurancebrokers.com
💬 WhatsApp: +30 210 0000000{portal_line}

Kind regards,
Christos Iatropoulos
Ashlar Insurance"""

def renewal_message_whatsapp(policy: dict, portal_url: str = "", lang: str = "el") -> str:
    """Generate short WhatsApp renewal message."""
    name   = policy.get("client_name","").split()[0] if policy.get("client_name") else "σας"
    ptype  = policy.get("policy_category","ασφάλεια")
    expiry = (policy.get("expiry_date","") or "").replace("-","/")
    prem   = policy.get("premium","")
    if lang == "el":
        msg = f"Γεια {name}, η {ptype} σας λήγει {expiry}."
        if prem: msg += f" Ασφάλιστρο {prem}€."
        if portal_url: msg += f"\n{portal_url}"
        msg += "\nΑνανέωση; Καλέστε +30 210 0000000 — Ashlar Insurance"
    else:
        msg = f"Hi {name}, your {ptype} policy expires {expiry}."
        if prem: msg += f" Premium {prem}."
        if portal_url: msg += f"\n{portal_url}"
        msg += "\nTo renew call +30 210 0000000 — Ashlar Insurance"
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# 4. COMMISSIONS TRACKER
# ══════════════════════════════════════════════════════════════════════════════

# Default commission rates per insurer (% of premium)
DEFAULT_COMMISSION_RATES = {
    "3P Insurance":  0.15,
    "Hellas Direct": 0.12,
    "Groupama":      0.18,
    "Generali":      0.18,
    "Ethniki":       0.16,
    "Morgan Price":  0.20,
    "NOW Health":    0.20,
    "Bupa Global":   0.20,
    "Safe Pet System": 0.15,
    "AXA":           0.17,
    "Interamerican": 0.17,
    "Eurolife":      0.16,
    "NN":            0.16,
    "Allianz":       0.17,
}

def calculate_commission(premium: float, insurer: str, rate_override: float = None) -> float:
    rate = rate_override or DEFAULT_COMMISSION_RATES.get(insurer, 0.15)
    return round(premium * rate, 2)

def commission_report(policies: list[dict]) -> dict:
    """Generate commission summary from policy list."""
    total_premium = 0; total_commission = 0
    by_insurer = {}
    for p in policies:
        try: prem = float(str(p.get("premium","0")).replace(",","").replace("€","").replace("£","").strip() or 0)
        except: prem = 0
        insurer = p.get("insurer","Unknown")
        comm = calculate_commission(prem, insurer)
        total_premium   += prem
        total_commission += comm
        if insurer not in by_insurer:
            by_insurer[insurer] = {"premium":0,"commission":0,"count":0}
        by_insurer[insurer]["premium"]    += prem
        by_insurer[insurer]["commission"] += comm
        by_insurer[insurer]["count"]      += 1
    return {
        "total_premium":    round(total_premium, 2),
        "total_commission": round(total_commission, 2),
        "by_insurer":       by_insurer,
        "policy_count":     len(policies),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. PORTFOLIO SUMMARY (for Claude prompt)
# ══════════════════════════════════════════════════════════════════════════════

def portfolio_summary_prompt(client_name: str, policies: list[dict], lang: str = "el") -> str:
    """Build prompt for Claude to generate portfolio summary."""
    policy_lines = "\n".join(
        f"- {p.get('policy_category','').title() or p.get('source','')} | "
        f"{p.get('insurer','')} | {p.get('policy_number','')} | "
        f"Premium: {p.get('premium','')} | Expiry: {p.get('expiry_date','')}"
        for p in policies
    ) or "No policies found."

    today = date.today().isoformat()
    if lang == "el":
        return f"""Δημιούργησε σύντομη επαγγελματική περίληψη χαρτοφυλακίου ασφαλίσεων για:
Πελάτης: {client_name}
Σημερινή ημ/νία: {today}

Ασφαλίσεις:
{policy_lines}

Περίληψη (3-4 προτάσεις): τι καλύπτει, ποιες λήγουν σύντομα, κενά κάλυψης που εντοπίζεις."""
    else:
        return f"""Generate a brief professional portfolio summary for:
Client: {client_name}
Today: {today}

Policies:
{policy_lines}

Summary (3-4 sentences): what's covered, what expires soon, any coverage gaps you notice."""
