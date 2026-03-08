"""
generate_claims.py
==================
Generates 1000 realistic healthcare claim JSON documents
for the MarkLogic Enterprise Claims Platform (MECP).

Output: data/bulk-claims/ directory (1000 .json files)

Usage:
    python scripts/generate_claims.py

Each file is named clm-XXXX.json starting from CLM-0011
(CLM-0001 through CLM-0010 are the original seed documents)
"""

import json
import random
import os
from datetime import datetime, timedelta

# ── Seed data ────────────────────────────────────────────────────────────────

PROVIDERS = [
    {"name": "Peachtree Clinic",         "city": "Atlanta",       "state": "GA"},
    {"name": "Macon Imaging",            "city": "Macon",         "state": "GA"},
    {"name": "Middle GA Ortho",          "city": "Warner Robins", "state": "GA"},
    {"name": "Savannah Pediatrics",      "city": "Savannah",      "state": "GA"},
    {"name": "Augusta ER",               "city": "Augusta",       "state": "GA"},
    {"name": "Athens Family Med",        "city": "Athens",        "state": "GA"},
    {"name": "Columbus Lab Services",    "city": "Columbus",      "state": "GA"},
    {"name": "Valdosta Cardiology",      "city": "Valdosta",      "state": "GA"},
    {"name": "Atlanta Neuro",            "city": "Atlanta",       "state": "GA"},
    {"name": "Marietta Primary Care",    "city": "Marietta",      "state": "GA"},
    {"name": "Gainesville Urgent Care",  "city": "Gainesville",   "state": "GA"},
    {"name": "Rome Regional Hospital",   "city": "Rome",          "state": "GA"},
    {"name": "Dalton Family Practice",   "city": "Dalton",        "state": "GA"},
    {"name": "Albany Medical Group",     "city": "Albany",        "state": "GA"},
    {"name": "Brunswick Coastal Care",   "city": "Brunswick",     "state": "GA"},
    {"name": "Statesboro Health Clinic", "city": "Statesboro",    "state": "GA"},
    {"name": "Carrollton Women Health",  "city": "Carrollton",    "state": "GA"},
    {"name": "LaGrange Primary Care",    "city": "LaGrange",      "state": "GA"},
    {"name": "Newnan Surgical Center",   "city": "Newnan",        "state": "GA"},
    {"name": "Douglasville Med Center",  "city": "Douglasville",  "state": "GA"},
]

MEMBERS = [f"M-{10001 + i}" for i in range(50)]

DIAGNOSIS_CODES = [
    ["J06.9"],   ["M54.5"],   ["I10"],     ["E11.9"],   ["Z00.00"],
    ["R07.9"],   ["G43.909"], ["I48.91"],  ["H66.90"],  ["S83.511A"],
    ["J18.9"],   ["N39.0"],   ["K21.0"],   ["F32.9"],   ["M79.3"],
    ["Z23"],     ["R51"],     ["J30.9"],   ["L40.0"],   ["E78.5"],
    ["I25.10"],  ["J44.1"],   ["N18.3"],   ["M17.11"],  ["F41.1"],
]

PROCEDURE_CODES = [
    ["99213"],        ["99214"],        ["99215"],        ["99395"],
    ["72148"],        ["93000"],        ["83036"],        ["29888"],
    ["70551"],        ["99285"],        ["93010", "99285"], ["99213", "93000"],
    ["80053"],        ["85025"],        ["71046"],        ["97110"],
    ["90834"],        ["99232"],        ["43239"],        ["27447"],
]

DENIAL_REASONS = [
    "Missing prior authorization",
    "Duplicate claim",
    "Coverage terminated",
    "Service not covered",
    "Referral required",
    "Claim filed after deadline",
    "Invalid procedure code",
    "Member not eligible on date of service",
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def random_date(start_days_ago=365, end_days_ago=1):
    today = datetime.today()
    start = today - timedelta(days=start_days_ago)
    end   = today - timedelta(days=end_days_ago)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")

def random_amount(base_min, base_max):
    billed  = round(random.uniform(base_min, base_max), 0)
    allowed = round(billed * random.uniform(0.60, 0.90), 0)
    paid    = round(allowed * random.uniform(0.85, 0.98), 0)
    return int(billed), int(allowed), int(paid)

# ── Generator ────────────────────────────────────────────────────────────────

def generate_claim(claim_number):
    claim_id  = f"CLM-{claim_number:04d}"
    provider  = random.choice(PROVIDERS)
    member_id = random.choice(MEMBERS)
    dx_codes  = random.choice(DIAGNOSIS_CODES)
    px_codes  = random.choice(PROCEDURE_CODES)

    service_date   = random_date(365, 2)
    submitted_date = (datetime.strptime(service_date, "%Y-%m-%d") +
                      timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")

    billed, allowed, paid = random_amount(80, 8000)

    # Status distribution: 50% PAID, 30% DENIED, 20% PENDING
    roll = random.random()
    if roll < 0.50:
        status = "PAID"
    elif roll < 0.80:
        status = "DENIED"
    else:
        status = "PENDING"

    claim = {
        "claimId":        claim_id,
        "memberId":       member_id,
        "provider":       provider["name"],
        "serviceDate":    service_date,
        "submittedDate":  submitted_date,
        "status":         status,
        "amountBilled":   billed,
        "amountAllowed":  allowed if status == "PAID" else 0,
        "amountPaid":     paid    if status == "PAID" else 0,
        "diagnosisCodes": dx_codes,
        "procedureCodes": px_codes,
        "facility": {
            "state": provider["state"],
            "city":  provider["city"]
        }
    }

    if status == "DENIED":
        claim["denialReason"] = random.choice(DENIAL_REASONS)

    return claim

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "bulk-claims"
    )
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating 1000 claim documents...")
    print(f"Output directory: {output_dir}")
    print()

    status_counts = {"PAID": 0, "DENIED": 0, "PENDING": 0}

    for i in range(1000):
        claim_number = i + 11  # starts at CLM-0011
        claim = generate_claim(claim_number)
        status_counts[claim["status"]] += 1

        filename = f"clm-{claim_number:04d}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(claim, f, indent=2)

    print(f"Generated 1000 claims successfully")
    print(f"  PAID:    {status_counts['PAID']}")
    print(f"  DENIED:  {status_counts['DENIED']}")
    print(f"  PENDING: {status_counts['PENDING']}")
    print()
    print(f"Files written to: {output_dir}")
    print(f"Ready for MLCP load on Day 9.")

if __name__ == "__main__":
    main()
