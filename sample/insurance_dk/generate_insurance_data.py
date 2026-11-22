"""Generates made-up data for a Danish consumer insurance company (10 CSV files).

3,000 customers, policies, coverages, claims and premium invoices from 2023-01-01 to 2025-12-31,
about 5% customer churn per year. Everything is invented. Run: python generate_insurance_data.py
"""

import csv
import datetime as dt
import math
import random
from pathlib import Path

OUT = Path(__file__).parent
rng = random.Random(20260101)
START, END = dt.date(2023, 1, 1), dt.date(2025, 12, 31)
N_CUSTOMERS = 3000
CHURN = 0.06  # tuned so the measured yearly churn lands near 5%
D = dt.timedelta


def pick(weighted):
    items, weights = zip(*weighted)
    return rng.choices(items, weights)[0]


def poisson(lam):
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def rand_date(a, b):
    return a + D(days=rng.randint(0, max((b - a).days, 0)))


def fold(s):
    return s.lower().translate(str.maketrans({"æ": "ae", "ø": "oe", "å": "aa", "é": "e", " ": ""}))


# ---- reference data --------------------------------------------------------------------
POSTAL = [  # zip, city, region, weight
    ("1050", "København K", "Hovedstaden", 3), ("2100", "København Ø", "Hovedstaden", 4), ("2200", "København N", "Hovedstaden", 4),
    ("2300", "København S", "Hovedstaden", 5), ("2400", "København NV", "Hovedstaden", 3), ("2450", "København SV", "Hovedstaden", 2),
    ("2500", "Valby", "Hovedstaden", 3), ("2600", "Glostrup", "Hovedstaden", 2), ("2630", "Taastrup", "Hovedstaden", 2),
    ("2650", "Hvidovre", "Hovedstaden", 2), ("2700", "Brønshøj", "Hovedstaden", 2), ("2750", "Ballerup", "Hovedstaden", 2),
    ("2770", "Kastrup", "Hovedstaden", 1), ("2800", "Kongens Lyngby", "Hovedstaden", 3), ("2900", "Hellerup", "Hovedstaden", 2),
    ("3000", "Helsingør", "Hovedstaden", 2), ("3400", "Hillerød", "Hovedstaden", 2), ("3600", "Frederikssund", "Hovedstaden", 1),
    ("4000", "Roskilde", "Sjælland", 3), ("4200", "Slagelse", "Sjælland", 2), ("4600", "Køge", "Sjælland", 2),
    ("4700", "Næstved", "Sjælland", 2), ("4800", "Nykøbing F", "Sjælland", 1),
    ("5000", "Odense C", "Syddanmark", 4), ("5200", "Odense V", "Syddanmark", 2), ("5700", "Svendborg", "Syddanmark", 1),
    ("6000", "Kolding", "Syddanmark", 2), ("6400", "Sønderborg", "Syddanmark", 1), ("6700", "Esbjerg", "Syddanmark", 3),
    ("7000", "Fredericia", "Syddanmark", 1), ("7100", "Vejle", "Syddanmark", 2),
    ("7400", "Herning", "Midtjylland", 2), ("7500", "Holstebro", "Midtjylland", 1), ("8000", "Aarhus C", "Midtjylland", 5),
    ("8200", "Aarhus N", "Midtjylland", 3), ("8260", "Viby J", "Midtjylland", 2), ("8600", "Silkeborg", "Midtjylland", 2),
    ("8700", "Horsens", "Midtjylland", 2), ("8800", "Viborg", "Midtjylland", 2),
    ("9000", "Aalborg", "Nordjylland", 4), ("9200", "Aalborg SV", "Nordjylland", 1), ("9400", "Nørresundby", "Nordjylland", 1),
    ("9800", "Hjørring", "Nordjylland", 1), ("9900", "Frederikshavn", "Nordjylland", 1),
]
FEMALE = "Anne Mette Kirsten Susanne Lene Pia Charlotte Camilla Louise Maria Julie Emma Ida Sofie Katrine Helle Birgitte Tina Line Anna".split()
MALE = "Jens Peter Michael Lars Henrik Thomas Søren Jan Morten Anders Rasmus Mikkel Jesper Martin Niels Mads Kasper Christian Frederik Oliver".split()
LAST = ("Nielsen Jensen Hansen Pedersen Andersen Christensen Larsen Sørensen Rasmussen Jørgensen Petersen Madsen "
        "Kristensen Olsen Thomsen Christiansen Poulsen Johansen Møller Mortensen Knudsen Jakobsen Mikkelsen Olesen").split()
STREETS = ("Vestergade Nørregade Østergade Søndergade Skovvej Strandvejen Parkvej Kirkevej Bakkevej Engvej Møllevej "
           "Skolegade Havnegade Storgade Banegårdsvej Birkevej Egevej Lærkevej Rosenvænget Solbakken Fasanvej Hovedgaden").split()
EMAIL_DOMAINS = [("gmail.com", 50), ("hotmail.com", 15), ("mail.dk", 10), ("outlook.dk", 10), ("yahoo.dk", 5),
                 ("jubii.dk", 5), ("tdcadsl.dk", 5)]

PRODUCTS = [  # id, name, category, weight for the first policy a customer buys
    (1, "Indboforsikring", "Bolig", 35), (2, "Bilforsikring", "Bil", 30), (3, "Husforsikring", "Bolig", 15),
    (4, "Ulykkesforsikring", "Person", 8), (5, "Rejseforsikring", "Person", 7), (6, "Dyreforsikring", "Dyr", 5),
]
# product -> (coverage name, type, base annual DKK, deductible DKK, sum insured range or None)
COVERS = {
    1: [("Brand og eksplosion", "Standard", 380, 0, (300_000, 1_200_000)),
        ("Tyveri og indbrud", "Standard", 520, 1500, (300_000, 1_200_000)),
        ("Vand- og ledningsskade", "Standard", 410, 1500, (300_000, 1_200_000)),
        ("Ansvar", "Standard", 190, 0, (5_000_000, 10_000_000)),
        ("Udvidet dækning", "Tilvalg", 740, 2500, (50_000, 300_000)),
        ("Cykeldækning", "Tilvalg", 260, 1000, (10_000, 40_000))],
    2: [("Ansvar", "Standard", 1400, 0, (10_000_000, 10_000_000)),
        ("Kasko", "Standard", 4200, 3500, (80_000, 600_000)),
        ("Delkasko", "Standard", 2100, 3500, (80_000, 600_000)),
        ("Vejhjælp", "Tilvalg", 620, 0, None),
        ("Rudeskade", "Tilvalg", 340, 0, None),
        ("Førerulykke", "Tilvalg", 310, 0, (250_000, 500_000))],
    3: [("Brand og eksplosion", "Standard", 2100, 0, (1_500_000, 6_000_000)),
        ("Storm og skybrud", "Standard", 1300, 2500, (1_500_000, 6_000_000)),
        ("Vandskade", "Standard", 1500, 3000, (1_500_000, 6_000_000)),
        ("Svamp og insekter", "Tilvalg", 820, 5000, (1_500_000, 6_000_000)),
        ("Ledningsskade", "Tilvalg", 900, 3000, (1_500_000, 6_000_000)),
        ("Husejeransvar", "Standard", 240, 0, (5_000_000, 10_000_000))],
    4: [("Død", "Standard", 360, 0, (100_000, 500_000)),
        ("Varigt mén", "Standard", 1250, 0, (500_000, 2_000_000)),
        ("Behandlingsudgifter", "Tilvalg", 280, 500, (20_000, 60_000))],
    5: [("Sygdom og hjemtransport", "Standard", 420, 0, (5_000_000, 5_000_000)),
        ("Rejseafbrydelse", "Standard", 360, 500, (30_000, 100_000)),
        ("Bagage", "Tilvalg", 180, 750, (10_000, 30_000)),
        ("Rejseansvar", "Tilvalg", 90, 0, (2_000_000, 5_000_000))],
    6: [("Dyrlægeudgifter", "Standard", 1800, 1000, (15_000, 50_000)),
        ("Ansvar", "Standard", 210, 0, (2_000_000, 5_000_000)),
        ("Livsforsikring", "Tilvalg", 260, 0, (5_000, 20_000)),
        ("Tyveri", "Tilvalg", 150, 0, (5_000, 15_000))],
}
# product -> (cause, accepted coverages, weight, typical loss DKK)
CAUSES = {
    1: [("Indbrud", ["Tyveri og indbrud"], 25, 14_000), ("Vandskade", ["Vand- og ledningsskade"], 30, 9_000),
        ("Brand", ["Brand og eksplosion"], 5, 60_000), ("Cykeltyveri", ["Cykeldækning", "Tyveri og indbrud"], 15, 7_000),
        ("Hærværk eller tab", ["Udvidet dækning"], 20, 4_500), ("Skade på andres ting", ["Ansvar"], 5, 8_000)],
    2: [("Kollision", ["Kasko"], 30, 32_000), ("Rudeskade", ["Rudeskade", "Delkasko", "Kasko"], 25, 2_800),
        ("Tyveri", ["Delkasko", "Kasko"], 6, 45_000), ("Vejhjælp", ["Vejhjælp"], 20, 1_400),
        ("Skade på andres bil", ["Ansvar"], 14, 18_000), ("Storm eller hærværk", ["Delkasko", "Kasko"], 5, 9_000)],
    3: [("Stormskade", ["Storm og skybrud"], 30, 42_000), ("Vandskade", ["Vandskade", "Ledningsskade"], 40, 55_000),
        ("Brand", ["Brand og eksplosion"], 5, 350_000), ("Svamp", ["Svamp og insekter"], 10, 70_000),
        ("Skade på andres ejendom", ["Husejeransvar"], 5, 25_000), ("Ledningsbrud", ["Ledningsskade"], 10, 38_000)],
    4: [("Fritidsulykke", ["Varigt mén", "Behandlingsudgifter"], 85, 22_000), ("Dødsfald", ["Død"], 1, 300_000),
        ("Arbejdsulykke", ["Varigt mén", "Behandlingsudgifter"], 14, 30_000)],
    5: [("Sygdom under rejsen", ["Sygdom og hjemtransport"], 40, 12_000), ("Rejseafbrydelse", ["Rejseafbrydelse"], 25, 14_000),
        ("Bortkommet bagage", ["Bagage"], 25, 4_500), ("Skade på andre", ["Rejseansvar"], 10, 6_000)],
    6: [("Sygdom hos dyret", ["Dyrlægeudgifter"], 70, 4_800), ("Ulykke", ["Dyrlægeudgifter"], 22, 7_500),
        ("Dyret er dødt", ["Livsforsikring"], 4, 8_000), ("Skade på andre", ["Ansvar"], 4, 5_000)],
}
CLAIM_FREQ = {1: 0.05, 2: 0.11, 3: 0.045, 4: 0.025, 5: 0.06, 6: 0.14}  # claims per policy-year
PAY_FREQ = [("Månedlig", 55, 12), ("Kvartalsvis", 15, 4), ("Halvårlig", 5, 2), ("Årlig", 25, 1)]
CHANNELS = [("Web", 42), ("Telefon", 22), ("Rådgiver", 20), ("Partner", 16)]
CANCEL_REASONS = [("Fandt en billigere pris", 38), ("Skiftet til et andet selskab", 24), ("Ikke længere behov", 14),
                  ("Fraflyttet", 8), ("Solgt bil eller bolig", 8), ("Utilfreds med skadebehandling", 6), ("Dødsfald", 2)]
CLAIM_CHANNELS = [("Selvbetjening på web", 50), ("Telefon", 35), ("App", 15)]

# ---- reference tables ------------------------------------------------------------------
postal_rows = [(z, c, r) for z, c, r, _ in POSTAL]
products = [(pid, name, cat) for pid, name, cat, _ in PRODUCTS]
coverages = []  # CoverageID, ProductID, Name, Type, BaseAnnualPremiumDKK, DefaultDeductibleDKK
cov_by_product = {}
cov_counter = 0
for pid, lst in COVERS.items():
    for name, typ, base, ded, srange in lst:
        cov_counter += 1
        coverages.append((cov_counter, pid, name, typ, base, ded))
        cov_by_product.setdefault(pid, {})[name] = (cov_counter, typ, base, ded, srange)

# ---- addresses and customers ---------------------------------------------------------
addresses = []  # AddressID, Street, HouseNumber, Floor, ZipCode


def new_address():
    zc = pick([(z, w) for z, _, _, w in POSTAL])
    floor = rng.choice(["st.", "1. th.", "1. tv.", "2. th.", "2. tv.", "3. th."]) if zc[:1] in "1289" and rng.random() < 0.45 else None
    aid = 50000 + len(addresses) + 1
    addresses.append((aid, rng.choice(STREETS), rng.randint(1, 140), floor, zc))
    return aid


customers, cust_info = [], {}
PHONE_PREFIXES = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 40, 41, 42, 50, 51, 52, 53, 60, 61, 71, 81, 91, 93]
for i in range(N_CUSTOMERS):
    cust_id = 100001 + i
    female = rng.random() < 0.51
    first = rng.choice(FEMALE if female else MALE)
    last = rng.choice(LAST)
    age = int(min(max(rng.gauss(46, 15), 18), 88))
    birth = dt.date(2025 - age, rng.randint(1, 12), rng.randint(1, 28))
    if i < 2300:
        signup = rand_date(dt.date(2008, 1, 1), dt.date(2022, 12, 31))
    else:
        signup = rand_date(START, END - D(days=60))
    if customers and rng.random() < 0.08:  # same household as an earlier customer
        prev = rng.choice(customers)
        aid = prev[7]
        last = prev[2] if rng.random() < 0.7 else last
    else:
        aid = new_address()
    email = None if rng.random() < 0.03 else \
        f"{fold(first)}.{fold(last)}{rng.choice(['', str(rng.randint(1, 99))])}@{pick(EMAIL_DOMAINS)}"
    phone = None if rng.random() < 0.08 else f"{rng.choice(PHONE_PREFIXES)}{rng.randint(100000, 999999)}"
    churn = None  # about 5% of the customers leave each year
    for year in range(2023, 2026):
        lo = max(dt.date(year, 1, 1), signup + D(days=30))
        hi = dt.date(year, 12, 31)
        if lo < hi and rng.random() < CHURN * ((hi - lo).days / 365):
            churn = rand_date(lo, hi)
            break
    customers.append((cust_id, first, last, birth.isoformat(), "K" if female else "M", email, phone, aid, signup.isoformat(),
                      "Opsagt" if churn else "Aktiv", churn.isoformat() if churn else None,
                      "Ja" if rng.random() < 0.62 else "Nej"))
    cust_info[cust_id] = {"signup": signup, "churn": churn, "aid": aid, "age": age,
                          "risk": min(max(rng.lognormvariate(0, 0.15), 0.8), 1.5)}

# ---- policies, coverages, invoices ------------------------------------------------------
policies, policy_covs, invoices = [], [], []
pol_meta = {}
cov_ded = {}  # (policy, coverage) -> deductible
inv_counter = 0


def add_policy(cust_id, pid, start):
    global inv_counter
    info = cust_info[cust_id]
    end, reason, status = None, None, "Aktiv"
    if info["churn"]:
        end, status, reason = info["churn"], "Opsagt", pick(CANCEL_REASONS)
    elif (END - max(start, START)).days > 60 and rng.random() < 0.03 * (END - max(start, START)).days / 365:
        end = rand_date(max(start, START) + D(days=30), END)  # this policy is cancelled, the customer stays
        status, reason = "Opsagt", pick(CANCEL_REASONS)
    if end and end < start:
        return
    pol_id = 700000 + len(policies) + 1
    freq_name, _, per_year = rng.choices(PAY_FREQ, [w for _, w, _ in PAY_FREQ])[0]
    insured = None
    if pid in (1, 3):
        insured = info["aid"] if (pid == 1 or rng.random() < 0.9) else new_address()
    policies.append((pol_id, f"DK-{start.year}-{pol_id - 600000:06d}", cust_id, pid, insured, start.isoformat(),
                     end.isoformat() if end else None, status, reason, freq_name, pick(CHANNELS)))
    held = []  # standard coverages always, optional ones now and then, one of Kasko/Delkasko for cars
    for name, (_, typ, _, _, _) in cov_by_product[pid].items():
        if pid == 2 and name in ("Kasko", "Delkasko"):
            continue
        if typ == "Standard" or rng.random() < 0.35:
            held.append(name)
    if pid == 2:
        held.append("Kasko" if rng.random() < 0.45 else "Delkasko")
    ageing = 1.0 + max(info["age"] - 55, 0) * 0.006
    total = 0
    for name in held:
        cov_id, typ, base, ded, srange = cov_by_product[pid][name]
        insured_sum = None
        if srange:
            insured_sum = int(round(rng.uniform(*srange), -3)) if srange[0] != srange[1] else srange[0]
        premium = int(round(base * info["risk"] * ageing * rng.uniform(0.95, 1.1)))
        deductible = ded if rng.random() < 0.8 else int(ded * 1.5)
        policy_covs.append((pol_id, cov_id, insured_sum, deductible, premium))
        cov_ded[(pol_id, cov_id)] = deductible
        total += premium
    pol_meta[pol_id] = {"cust": cust_id, "pid": pid, "start": start, "end": end, "held": held}

    step = 12 // per_year  # months per invoice
    period_start = start
    while period_start <= END:
        if end and period_start > end:
            break
        months = period_start.month - 1 + step
        period_end = dt.date(period_start.year + months // 12, months % 12 + 1, 1) - D(days=1)
        if period_start >= START:
            last_day = min(period_end, end) if end else period_end
            frac = ((last_day - period_start).days + 1) / ((period_end - period_start).days + 1)
            amount = int(round(total * frac / per_year))
            inv_counter += 1
            invoice_date = max(period_start - D(days=14), START)
            due = invoice_date + D(days=14)
            r = rng.random()
            if r < 0.93:
                paid, inv_status = invoice_date + D(days=rng.randint(0, 14)), "Betalt"
            elif r < 0.985:
                paid, inv_status = due + D(days=rng.randint(1, 40)), "Betalt"
            else:
                paid, inv_status = None, "Forfalden"
            if paid and paid > END:
                paid, inv_status = None, "Åben"
            if not paid and due >= END - D(days=10):
                inv_status = "Åben"
            invoices.append((800000 + inv_counter, pol_id, invoice_date.isoformat(), due.isoformat(), period_start.isoformat(),
                             last_day.isoformat(), amount, paid.isoformat() if paid else None, inv_status))
        period_start = period_end + D(days=1)


for c in customers:
    cust_id, signup = c[0], cust_info[c[0]]["signup"]
    first_pid = pick([(p[0], p[3]) for p in PRODUCTS])
    add_policy(cust_id, first_pid, signup)
    owned = {first_pid}
    for _ in range(poisson(0.9)):
        options = [(p[0], p[3]) for p in PRODUCTS if p[0] not in owned or (p[0] == 2 and rng.random() < 0.15)]
        if not options or signup + D(days=60) > END:
            break
        pid = pick(options)
        owned.add(pid)
        add_policy(cust_id, pid, rand_date(signup + D(days=60), END))

# ---- claims and payments ------------------------------------------------------------
claims, payments = [], []
for pol_id, m in sorted(pol_meta.items()):
    lo, hi = max(m["start"], START), min(m["end"] or END, END)
    if hi <= lo:
        continue
    years = ((hi - lo).days + 1) / 365
    for _ in range(poisson(CLAIM_FREQ[m["pid"]] * years)):
        options = [o for o in CAUSES[m["pid"]] if any(x in m["held"] for x in o[1])]
        if not options:
            continue
        cause, covs, _, typical = rng.choices(options, [o[2] for o in options])[0]
        covered = next(x for x in covs if x in m["held"])
        cov_id = cov_by_product[m["pid"]][covered][0]
        loss = int(round(typical * rng.lognormvariate(0, 0.7), -1 if typical < 10000 else -2))
        loss_date = rand_date(lo, hi)
        reported = min(loss_date + D(days=poisson(1.5) if rng.random() < 0.8 else rng.randint(5, 30)), END)
        age_days = (END - reported).days
        if age_days < 60 and rng.random() < 0.7:
            status, closed = "Åben", None
        elif rng.random() < 0.11:
            status, closed = "Afvist", min(reported + D(days=rng.randint(3, 40)), END)
        else:
            status, closed = "Afsluttet", min(reported + D(days=rng.randint(4, 120)), END)
            if closed >= END and age_days < 60:
                status, closed = "Åben", None
        claim_id = 900000 + len(claims) + 1
        claims.append((claim_id, pol_id, loss_date.isoformat(), reported.isoformat(), cause, status,
                       closed.isoformat() if closed else None, loss, pick(CLAIM_CHANNELS)))
        payable = max(loss - cov_ded[(pol_id, cov_id)], 0)
        if status == "Afvist" or payable == 0:
            continue
        n_pay = 1 if payable < 8000 else rng.choice([1, 1, 2, 3])
        if status == "Åben":
            n_pay = 1 if rng.random() < 0.35 else 0
        for k in range(n_pay):
            pay_date = (closed or reported + D(days=rng.randint(5, 40))) - D(days=(n_pay - 1 - k) * rng.randint(2, 20))
            pay_date = min(max(pay_date, reported), END)
            payee = "Kunde" if m["pid"] in (4, 5, 6) or loss < 6000 else rng.choice(["Kunde", "Værksted", "Håndværker", "Leverandør"])
            payments.append((950000 + len(payments) + 1, claim_id, cov_id, pay_date.isoformat(),
                             int(round(payable / n_pay)), payee))


# ---- write ----------------------------------------------------------------------------
def write(name, header, rows):
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows):,} rows")


write("PostalCodes", ["ZipCode", "City", "Region"], postal_rows)
write("Addresses", ["AddressID", "Street", "HouseNumber", "Floor", "ZipCode"], addresses)
write("Customers", ["CustomerID", "FirstName", "LastName", "BirthDate", "Gender", "Email", "Phone", "AddressID", "SignupDate",
                    "CustomerStatus", "ChurnDate", "MarketingConsent"], customers)
write("Products", ["ProductID", "ProductName", "ProductCategory"], products)
write("Coverages", ["CoverageID", "ProductID", "CoverageName", "CoverageType", "BaseAnnualPremiumDKK",
                    "DefaultDeductibleDKK"], coverages)
write("Policies", ["PolicyID", "PolicyNumber", "CustomerID", "ProductID", "InsuredAddressID", "StartDate", "EndDate",
                   "PolicyStatus", "CancellationReason", "PaymentFrequency", "SalesChannel"], policies)
write("PolicyCoverages", ["PolicyID", "CoverageID", "SumInsuredDKK", "DeductibleDKK", "AnnualPremiumDKK"], policy_covs)
write("Claims", ["ClaimID", "PolicyID", "LossDate", "ReportedDate", "ClaimCause", "ClaimStatus", "ClosedDate",
                 "EstimatedLossDKK", "ReportedVia"], claims)
write("ClaimPayments", ["PaymentID", "ClaimID", "CoverageID", "PaymentDate", "AmountDKK", "PayeeType"], payments)
write("PremiumInvoices", ["InvoiceID", "PolicyID", "InvoiceDate", "DueDate", "PeriodStart", "PeriodEnd", "AmountDKK",
                          "PaidDate", "InvoiceStatus"], invoices)
