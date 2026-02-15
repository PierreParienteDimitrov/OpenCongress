"""
Mapping of FEC free-text occupation strings to standardized industry categories.

Since the OpenSecrets API was discontinued in April 2025, we use the FEC's
``/schedules/schedule_a/by_occupation/`` endpoint which returns contributions
grouped by free-text occupation.  This module maps those raw strings to broader
industry categories modeled after the OpenSecrets/CRP classification scheme.
"""

# Exact-match mapping: UPPERCASE occupation → industry category.
OCCUPATION_TO_INDUSTRY: dict[str, str] = {
    # ── Health Professionals ──────────────────────────────────────────
    "PHYSICIAN": "Health Professionals",
    "DOCTOR": "Health Professionals",
    "DENTIST": "Health Professionals",
    "NURSE": "Health Professionals",
    "REGISTERED NURSE": "Health Professionals",
    "NURSE PRACTITIONER": "Health Professionals",
    "PHARMACIST": "Health Professionals",
    "SURGEON": "Health Professionals",
    "VETERINARIAN": "Health Professionals",
    "OPTOMETRIST": "Health Professionals",
    "PSYCHOLOGIST": "Health Professionals",
    "PSYCHIATRIST": "Health Professionals",
    "THERAPIST": "Health Professionals",
    "CHIROPRACTOR": "Health Professionals",
    "PHYSICAL THERAPIST": "Health Professionals",
    "MEDICAL DOCTOR": "Health Professionals",
    "RADIOLOGIST": "Health Professionals",
    "ANESTHESIOLOGIST": "Health Professionals",
    "CARDIOLOGIST": "Health Professionals",
    "DERMATOLOGIST": "Health Professionals",
    "NEUROLOGIST": "Health Professionals",
    "ONCOLOGIST": "Health Professionals",
    "ORTHOPEDIC SURGEON": "Health Professionals",
    "PEDIATRICIAN": "Health Professionals",
    "PATHOLOGIST": "Health Professionals",
    "OPHTHALMOLOGIST": "Health Professionals",
    # ── Lawyers & Lobbyists ───────────────────────────────────────────
    "ATTORNEY": "Lawyers & Lobbyists",
    "LAWYER": "Lawyers & Lobbyists",
    "LOBBYIST": "Lawyers & Lobbyists",
    "LEGAL COUNSEL": "Lawyers & Lobbyists",
    "PARALEGAL": "Lawyers & Lobbyists",
    "JUDGE": "Lawyers & Lobbyists",
    "TRIAL ATTORNEY": "Lawyers & Lobbyists",
    "PARTNER": "Lawyers & Lobbyists",
    "GOVERNMENT RELATIONS": "Lawyers & Lobbyists",
    # ── Finance, Insurance & Real Estate ──────────────────────────────
    "BANKER": "Finance, Insurance & Real Estate",
    "INVESTMENT BANKER": "Finance, Insurance & Real Estate",
    "FINANCIAL ADVISOR": "Finance, Insurance & Real Estate",
    "FINANCIAL ANALYST": "Finance, Insurance & Real Estate",
    "FINANCIAL CONSULTANT": "Finance, Insurance & Real Estate",
    "FINANCIAL PLANNER": "Finance, Insurance & Real Estate",
    "ACCOUNTANT": "Finance, Insurance & Real Estate",
    "CPA": "Finance, Insurance & Real Estate",
    "INSURANCE AGENT": "Finance, Insurance & Real Estate",
    "INSURANCE": "Finance, Insurance & Real Estate",
    "HEDGE FUND MANAGER": "Finance, Insurance & Real Estate",
    "INVESTOR": "Finance, Insurance & Real Estate",
    "STOCKBROKER": "Finance, Insurance & Real Estate",
    "VENTURE CAPITALIST": "Finance, Insurance & Real Estate",
    "PORTFOLIO MANAGER": "Finance, Insurance & Real Estate",
    "ACTUARY": "Finance, Insurance & Real Estate",
    # ── Real Estate ───────────────────────────────────────────────────
    "REAL ESTATE": "Real Estate",
    "REAL ESTATE AGENT": "Real Estate",
    "REAL ESTATE BROKER": "Real Estate",
    "REALTOR": "Real Estate",
    "REAL ESTATE DEVELOPER": "Real Estate",
    "PROPERTY MANAGER": "Real Estate",
    "REAL ESTATE INVESTOR": "Real Estate",
    # ── Tech & Internet ───────────────────────────────────────────────
    "SOFTWARE ENGINEER": "Tech & Internet",
    "SOFTWARE DEVELOPER": "Tech & Internet",
    "PROGRAMMER": "Tech & Internet",
    "COMPUTER SCIENTIST": "Tech & Internet",
    "DATA SCIENTIST": "Tech & Internet",
    "INFORMATION TECHNOLOGY": "Tech & Internet",
    "IT MANAGER": "Tech & Internet",
    "WEB DEVELOPER": "Tech & Internet",
    "PRODUCT MANAGER": "Tech & Internet",
    "SYSTEMS ENGINEER": "Tech & Internet",
    "NETWORK ENGINEER": "Tech & Internet",
    "DATABASE ADMINISTRATOR": "Tech & Internet",
    # ── Education ─────────────────────────────────────────────────────
    "TEACHER": "Education",
    "PROFESSOR": "Education",
    "EDUCATOR": "Education",
    "SCHOOL ADMINISTRATOR": "Education",
    "PRINCIPAL": "Education",
    "ACADEMIC": "Education",
    "LIBRARIAN": "Education",
    # ── Energy & Natural Resources ────────────────────────────────────
    "GEOLOGIST": "Energy & Natural Resources",
    "PETROLEUM ENGINEER": "Energy & Natural Resources",
    "MINING ENGINEER": "Energy & Natural Resources",
    # ── Construction ──────────────────────────────────────────────────
    "CONTRACTOR": "Construction",
    "GENERAL CONTRACTOR": "Construction",
    "BUILDER": "Construction",
    "ARCHITECT": "Construction",
    "CIVIL ENGINEER": "Construction",
    "PLUMBER": "Construction",
    "ELECTRICIAN": "Construction",
    "CARPENTER": "Construction",
    # ── Agribusiness ──────────────────────────────────────────────────
    "FARMER": "Agribusiness",
    "RANCHER": "Agribusiness",
    "AGRICULTURAL": "Agribusiness",
    # ── Defense ────────────────────────────────────────────────────────
    "MILITARY": "Defense",
    "DEFENSE CONTRACTOR": "Defense",
    # ── Transportation ────────────────────────────────────────────────
    "PILOT": "Transportation",
    "AIRLINE PILOT": "Transportation",
    "TRUCK DRIVER": "Transportation",
    "TRANSPORTATION": "Transportation",
    # ── Communications & Electronics ──────────────────────────────────
    "JOURNALIST": "Communications & Electronics",
    "WRITER": "Communications & Electronics",
    "AUTHOR": "Communications & Electronics",
    "EDITOR": "Communications & Electronics",
    "PUBLISHER": "Communications & Electronics",
    "FILMMAKER": "Communications & Electronics",
    "PRODUCER": "Communications & Electronics",
    # ── Government & Public Admin ─────────────────────────────────────
    "GOVERNMENT EMPLOYEE": "Government & Public Admin",
    "PUBLIC SERVANT": "Government & Public Admin",
    "CIVIL SERVANT": "Government & Public Admin",
    "GOVERNMENT": "Government & Public Admin",
    "FIREFIGHTER": "Government & Public Admin",
    "POLICE OFFICER": "Government & Public Admin",
    "LAW ENFORCEMENT": "Government & Public Admin",
    # ── Labor ─────────────────────────────────────────────────────────
    "UNION REPRESENTATIVE": "Labor",
    "UNION OFFICIAL": "Labor",
    # ── Miscellaneous Business ────────────────────────────────────────
    "CONSULTANT": "Miscellaneous Business",
    "BUSINESS CONSULTANT": "Miscellaneous Business",
    "MANAGEMENT CONSULTANT": "Miscellaneous Business",
    "EXECUTIVE": "Miscellaneous Business",
    "CEO": "Miscellaneous Business",
    "CFO": "Miscellaneous Business",
    "COO": "Miscellaneous Business",
    "PRESIDENT": "Miscellaneous Business",
    "VICE PRESIDENT": "Miscellaneous Business",
    "MANAGER": "Miscellaneous Business",
    "BUSINESS OWNER": "Miscellaneous Business",
    "OWNER": "Miscellaneous Business",
    "ENTREPRENEUR": "Miscellaneous Business",
    "SMALL BUSINESS OWNER": "Miscellaneous Business",
    "SALES": "Miscellaneous Business",
    "SALESMAN": "Miscellaneous Business",
    "MARKETING": "Miscellaneous Business",
    # ── Retired ───────────────────────────────────────────────────────
    "RETIRED": "Retired",
    "RETIREE": "Retired",
    # ── Self-Employed ─────────────────────────────────────────────────
    "SELF-EMPLOYED": "Self-Employed",
    "SELF EMPLOYED": "Self-Employed",
    # ── Non-classifiable ──────────────────────────────────────────────
    "HOMEMAKER": "Other",
    "NOT EMPLOYED": "Other",
    "NONE": "Other",
    "STUDENT": "Other",
    "UNEMPLOYED": "Other",
    "N/A": "Other",
    "INFORMATION REQUESTED": "Other",
    "INFORMATION REQUESTED PER BEST EFFORTS": "Other",
}

# Substring fallback: if occupation CONTAINS the keyword, map to industry.
# Checked in order; first match wins.
_KEYWORD_FALLBACKS: list[tuple[str, str]] = [
    # Health
    ("PHYSICIAN", "Health Professionals"),
    ("NURS", "Health Professionals"),
    ("MEDIC", "Health Professionals"),
    ("PHARM", "Health Professionals"),
    ("DENTAL", "Health Professionals"),
    ("DENT ", "Health Professionals"),
    ("SURG", "Health Professionals"),
    ("HEALTH", "Health Professionals"),
    ("THERAP", "Health Professionals"),
    ("CHIRO", "Health Professionals"),
    # Law
    ("ATTORNEY", "Lawyers & Lobbyists"),
    ("LAWYER", "Lawyers & Lobbyists"),
    ("LAW FIRM", "Lawyers & Lobbyists"),
    ("LEGAL", "Lawyers & Lobbyists"),
    ("LOBBY", "Lawyers & Lobbyists"),
    # Finance
    ("FINANC", "Finance, Insurance & Real Estate"),
    ("BANK", "Finance, Insurance & Real Estate"),
    ("INSUR", "Finance, Insurance & Real Estate"),
    ("ACCOUNT", "Finance, Insurance & Real Estate"),
    ("INVEST", "Finance, Insurance & Real Estate"),
    ("HEDGE", "Finance, Insurance & Real Estate"),
    # Real Estate
    ("REAL ESTATE", "Real Estate"),
    ("REALTOR", "Real Estate"),
    ("PROPERTY", "Real Estate"),
    # Tech
    ("SOFTWARE", "Tech & Internet"),
    ("COMPUTER", "Tech & Internet"),
    ("PROGRAMM", "Tech & Internet"),
    ("DATA SCI", "Tech & Internet"),
    # Education
    ("TEACH", "Education"),
    ("PROFESSOR", "Education"),
    ("EDUCAT", "Education"),
    # Energy
    ("ENERGY", "Energy & Natural Resources"),
    ("OIL ", "Energy & Natural Resources"),
    ("GAS ", "Energy & Natural Resources"),
    ("MINING", "Energy & Natural Resources"),
    ("PETROLEUM", "Energy & Natural Resources"),
    # Construction
    ("CONSTRUCT", "Construction"),
    ("ARCHITECT", "Construction"),
    ("PLUMB", "Construction"),
    ("ELECTRI", "Construction"),
    # Agribusiness
    ("FARM", "Agribusiness"),
    ("RANCH", "Agribusiness"),
    ("AGRIC", "Agribusiness"),
    # Defense
    ("MILITARY", "Defense"),
    ("DEFENSE", "Defense"),
    # Transportation
    ("TRANSPORT", "Transportation"),
    ("TRUCK", "Transportation"),
    ("PILOT", "Transportation"),
    ("AIRLINE", "Transportation"),
    # Communications
    ("JOURNALIST", "Communications & Electronics"),
    ("PUBLISH", "Communications & Electronics"),
    ("MEDIA", "Communications & Electronics"),
    # Government
    ("GOVERNMENT", "Government & Public Admin"),
    ("FIREFIGHT", "Government & Public Admin"),
    ("POLICE", "Government & Public Admin"),
    # Retired
    ("RETIRE", "Retired"),
    # Self-employed
    ("SELF-EMPLOY", "Self-Employed"),
    ("SELF EMPLOY", "Self-Employed"),
    # Catch-all non-classifiable
    ("HOMEMAKER", "Other"),
    ("NOT EMPLOY", "Other"),
    ("STUDENT", "Other"),
    ("UNEMPLOY", "Other"),
    ("INFORMATION REQUESTED", "Other"),
]


def map_occupation_to_industry(occupation: str) -> str:
    """Map a raw FEC occupation string to a standardized industry category.

    Strategy: normalize → exact match → substring fallback → ``"Other"``.
    """
    if not occupation:
        return "Other"

    normalized = occupation.upper().strip()

    # Exact match
    industry = OCCUPATION_TO_INDUSTRY.get(normalized)
    if industry:
        return industry

    # Substring fallback
    for keyword, industry_name in _KEYWORD_FALLBACKS:
        if keyword in normalized:
            return industry_name

    return "Other"
