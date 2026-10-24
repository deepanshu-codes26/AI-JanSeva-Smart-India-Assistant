import os
import re
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "janseva.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "")
if not app.config["SECRET_KEY"]:
    # Development fallback only; production deployment must set SECRET_KEY.
    app.config["SECRET_KEY"] = "dev-only-change-this-key"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

SCHEMES = [
    ("National Scholarship Portal","Education","Scholarship discovery and application information for eligible students.","https://scholarships.gov.in/","students"),
    ("PM-YASASVI","Education","Scholarship support for eligible students under notified guidelines.","https://yet.nta.ac.in/","students"),
    ("Central Sector Scholarship","Education","Scholarship programme for eligible college and university students.","https://scholarships.gov.in/","students"),
    ("Samagra Shiksha","Education","School education programme supporting access, equity and quality.","https://samagra.education.gov.in/","students"),
    ("Aadhaar Services","Documents","Official Aadhaar enrolment, update and related services.","https://uidai.gov.in/","documents"),
    ("DigiLocker","Documents","Access and manage eligible digital documents and certificates.","https://www.digilocker.gov.in/","documents"),
    ("Passport Seva","Documents","Passport application and related citizen services.","https://www.passportindia.gov.in/","documents"),
    ("Parivahan Sewa","Documents","Transport services including driving licence and vehicle-related services.","https://parivahan.gov.in/","documents"),
    ("Ayushman Bharat PM-JAY","Healthcare","Health coverage information for eligible beneficiaries under current programme rules.","https://pmjay.gov.in/","healthcare"),
    ("Ayushman Arogya Mandirs","Healthcare","Primary healthcare services through the public health system.","https://ab-hwc.nhp.gov.in/","healthcare"),
    ("Mission Indradhanush","Healthcare","Immunisation programme information for eligible children and pregnant women.","https://mohfw.gov.in/","healthcare"),
    ("PM Matru Vandana Yojana","Healthcare","Maternity benefit scheme information under current guidelines.","https://pmmvy.wcd.gov.in/","healthcare"),
    ("PM-KISAN","Farmers","Income-support scheme information for eligible landholding farmer families.","https://pmkisan.gov.in/","farmers"),
    ("PM Fasal Bima Yojana","Farmers","Crop insurance information for notified crops and areas.","https://pmfby.gov.in/","farmers"),
    ("Kisan Credit Card","Farmers","Institutional credit information for eligible farmers and related groups.","https://www.myscheme.gov.in/","farmers"),
    ("PM Krishi Sinchayee Yojana","Farmers","Irrigation and water-use efficiency programme information.","https://pmksy.gov.in/","farmers"),
    ("Soil Health Card","Farmers","Soil testing and nutrient-management information for farmers.","https://soilhealth.dac.gov.in/","farmers"),
    ("PMAY-Urban","Housing","Urban housing programme information under applicable guidelines.","https://pmay-urban.gov.in/","housing"),
    ("PMAY-Gramin","Housing","Rural housing assistance information under current programme rules.","https://pmayg.nic.in/","housing"),
    ("MGNREGA","Jobs","Rural wage-employment programme information and official services.","https://nrega.nic.in/","jobs"),
    ("PMKVY","Jobs","Skill training and certification programme information.","https://www.skillindia.gov.in/","jobs"),
    ("Skill India","Jobs","Skills and training programme information.","https://www.skillindia.gov.in/","jobs"),
    ("National Career Service","Jobs","Employment, career counselling and job-search services.","https://www.ncs.gov.in/","jobs"),
    ("Mission Shakti","Women","Women’s safety, security and empowerment programme information.","https://wcd.gov.in/","women"),
    ("Beti Bachao Beti Padhao","Women","Programme supporting the value, protection and education of the girl child.","https://wcd.gov.in/","women"),
    ("Mission Vatsalya","Women","Child protection and welfare programme information.","https://wcd.gov.in/","women"),
    ("POSHAN Abhiyaan","Women","Nutrition-related programme information for women and children.","https://poshanabhiyaan.gov.in/","women"),
    ("Pradhan Mantri Jan-Dhan Yojana","Finance","Financial inclusion and basic banking information.","https://pmjdy.gov.in/","finance"),
    ("PM Jeevan Jyoti Bima Yojana","Finance","Life insurance scheme information; check current age and premium conditions.","https://jansuraksha.gov.in/","finance"),
    ("PM Suraksha Bima Yojana","Finance","Accident insurance scheme information under current terms.","https://jansuraksha.gov.in/","finance"),
    ("Atal Pension Yojana","Finance","Pension scheme information for eligible subscribers.","https://npscra.nsdl.co.in/","finance"),
    ("National Social Assistance Programme","Finance","Social assistance and pension programme information.","https://nsap.nic.in/","finance"),
    ("Startup India","Business","Startup recognition, learning resources and ecosystem support.","https://www.startupindia.gov.in/","business"),
    ("Pradhan Mantri MUDRA Yojana","Business","Micro-enterprise lending information through participating lenders.","https://www.mudra.org.in/","business"),
    ("MSME Support","Business","Official MSME registration and support information.","https://msme.gov.in/","business"),
    ("Digital India","Digital","Digital public services and digital infrastructure information.","https://www.digitalindia.gov.in/","digital"),
    ("Swachh Bharat Mission","Digital","Sanitation and cleanliness programme information.","https://swachhbharatmission.ddws.gov.in/","digital"),
    ("Jal Jeevan Mission","Digital","Rural household tap-water programme information.","https://jaljeevanmission.gov.in/","digital"),
    ("PM Surya Ghar","Digital","Residential rooftop solar scheme information.","https://pmsuryaghar.gov.in/","digital"),
    ("National Food Security","Digital","Food security and ration-related information; verify state-specific processes.","https://nfsa.gov.in/","digital"),
    ("Disability Support","Digital","Disability-related certificates, benefits and services information.","https://swavlambancard.gov.in/","digital"),
]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS saved_schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        scheme_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, scheme_name),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    db.commit()
    db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("इस सुविधा के लिए पहले लॉगिन करें।", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def api_login_required(view):
    """Require authentication for JSON endpoints without returning HTML redirects."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Please log in to use this feature.", "login_required": True}), 401
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user():
    return {"current_user": session.get("user_name")}

@app.route("/")
@login_required
def index():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "all").strip().lower()
    schemes = SCHEMES
    if query:
        schemes = [s for s in schemes if query.lower() in " ".join(s[:4]).lower()]
    if category != "all":
        schemes = [s for s in schemes if s[1].lower() == category]
    saved = set()
    if session.get("user_id"):
        rows = get_db().execute("SELECT scheme_name FROM saved_schemes WHERE user_id=?", (session["user_id"],)).fetchall()
        saved = {r["scheme_name"] for r in rows}
    categories = sorted({s[1] for s in SCHEMES})
    return render_template("index.html", schemes=schemes, categories=categories,
                           query=query, selected_category=category, saved=saved, total=len(SCHEMES))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or "@" not in email or len(password) < 8:
            flash("सही नाम/email भरें और password कम से कम 8 characters का रखें।", "error")
            return render_template("auth.html", mode="register")
        try:
            db = get_db()
            cur = db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                             (name, email, generate_password_hash(password)))
            db.commit()
            session["user_id"] = cur.lastrowid
            session["user_name"] = name
            flash("आपका account बन गया है।", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("यह email पहले से registered है। Login करें।", "error")
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("लॉगिन सफल रहा।", "success")
            return redirect(url_for("index"))
        flash("Email या password सही नहीं है।", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    flash("आप logout हो गए हैं।", "info")
    return redirect(url_for("index"))

@app.route("/save/<path:scheme_name>", methods=["POST"])
@login_required
def save_scheme(scheme_name):
    known = {s[0] for s in SCHEMES}
    if scheme_name not in known:
        flash("यह योजना सूची में नहीं मिली।", "error")
        return redirect(url_for("index"))
    db = get_db()
    existing = db.execute("SELECT id FROM saved_schemes WHERE user_id=? AND scheme_name=?",
                          (session["user_id"], scheme_name)).fetchone()
    if existing:
        db.execute("DELETE FROM saved_schemes WHERE user_id=? AND scheme_name=?",
                   (session["user_id"], scheme_name))
        flash("योजना saved list से हटा दी गई।", "info")
    else:
        db.execute("INSERT OR IGNORE INTO saved_schemes(user_id,scheme_name) VALUES(?,?)",
                   (session["user_id"], scheme_name))
        flash("योजना आपकी saved list में जोड़ दी गई।", "success")
    db.commit()
    return redirect(url_for("index"))

@app.route("/saved")
@login_required
def saved():
    rows = get_db().execute("SELECT scheme_name FROM saved_schemes WHERE user_id=? ORDER BY created_at DESC",
                            (session["user_id"],)).fetchall()
    names = {r["scheme_name"] for r in rows}
    schemes = [s for s in SCHEMES if s[0] in names]
    return render_template("saved.html", schemes=schemes)

@app.route("/api/eligibility", methods=["POST"])
@api_login_required
def eligibility():
    data = request.get_json(silent=True) or request.form
    try:
        age = int(data.get("age", ""))
        income = int(data.get("income", ""))
    except (ValueError, TypeError):
        return jsonify({"error": "उम्र और वार्षिक आय सही संख्या में भरें।"}), 400
    occupation = str(data.get("occupation", "")).strip().lower()
    state = str(data.get("state", "")).strip()
    category = str(data.get("category", "")).strip()
    if not (0 <= age <= 120) or income < 0 or not occupation or not state:
        return jsonify({"error": "उम्र, आय, व्यवसाय और राज्य की सही जानकारी भरें।"}), 400
    suggestions = []
    def add(title, reason, url):
        suggestions.append({"title": title, "reason": reason, "url": url})
    if occupation == "student":
        add("National Scholarship Portal", "छात्रवृत्ति के लिए कोर्स, आय, श्रेणी और राज्य के अनुसार उपलब्ध विकल्प जाँचें।", "https://scholarships.gov.in/")
        if category.lower() in ["obc", "sc", "st", "ews"]:
            add("PM-YASASVI / संबंधित छात्रवृत्ति", "आपकी श्रेणी के अनुसार उपलब्धता और मौजूदा नियम आधिकारिक पोर्टल पर जाँचें।", "https://yet.nta.ac.in/")
    if occupation == "farmer":
        add("PM-KISAN", "भूमि रिकॉर्ड और अन्य शर्तों सहित वर्तमान पात्रता जाँचें।", "https://pmkisan.gov.in/")
        add("PM Fasal Bima Yojana", "राज्य, notified crop और enrollment period के अनुसार जानकारी जाँचें।", "https://pmfby.gov.in/")
    if occupation in ["employee", "job seeker", "unemployed"]:
        add("National Career Service", "रोजगार और career services देखें।", "https://www.ncs.gov.in/")
        add("Skill India", "उपलब्ध skill training programmes देखें।", "https://www.skillindia.gov.in/")
    if occupation in ["business", "self-employed"]:
        add("MUDRA / MSME Support", "व्यवसाय के प्रकार और lender rules के अनुसार विकल्प जाँचें।", "https://www.mudra.org.in/")
    if age >= 60:
        add("National Social Assistance Programme", "पेंशन की आयु, आय और राज्य-विशिष्ट शर्तें जाँचें।", "https://nsap.nic.in/")
    if income <= 300000:
        add("राज्य और आय-आधारित सहायता", f"{state} की आधिकारिक वेबसाइट पर आय-आधारित योजनाएँ और प्रमाणपत्र नियम देखें।", "https://www.myscheme.gov.in/")
    if not suggestions:
        add("myScheme", "अपनी परिस्थितियों के आधार पर केंद्रीय और राज्य योजनाओं को खोजें।", "https://www.myscheme.gov.in/")
    return jsonify({
        "disclaimer": "ये केवल शुरुआती सुझाव हैं, पात्रता की आधिकारिक पुष्टि नहीं। योजना के मौजूदा नियम और दस्तावेज़ संबंधित सरकारी पोर्टल पर जाँचें।",
        "suggestions": suggestions
    })



def janseva_search_schemes(query, category=""):
    """Search the local, curated scheme catalogue; returns only catalogue facts."""
    query = str(query or "").strip().lower()[:160]
    category = str(category or "").strip().lower()[:40]
    terms = [x for x in query.split() if len(x) > 2]
    matches = []
    for name, cat, description, url, audience in SCHEMES:
        haystack = f"{name} {cat} {description} {audience}".lower()
        if category and category not in cat.lower() and category not in audience.lower():
            continue
        score = sum(1 for term in terms if term in haystack)
        if score or not terms:
            matches.append((score, {"name": name, "category": cat, "description": description, "official_url": url}))
    matches.sort(key=lambda item: item[0], reverse=True)
    return {"results": [x[1] for x in matches[:6]], "note": "Catalogue descriptions are guidance only; verify current rules on the official portal."}


def janseva_get_scheme_details(name):
    """Return a scheme record from the local catalogue by matching its name."""
    needle = str(name or "").strip().lower()[:120]
    for title, category, description, url, audience in SCHEMES:
        if needle and (needle == title.lower() or needle in title.lower() or title.lower() in needle):
            return {"name": title, "category": category, "description": description,
                    "official_url": url, "intended_audience": audience,
                    "verification": "Current eligibility, benefits, deadlines and required documents must be checked on the official portal."}
    return {"error": "Scheme not found in the local catalogue. Try searching the catalogue or myScheme.",
            "official_discovery_portal": "https://www.myscheme.gov.in/"}


def janseva_document_checklist(service):
    """Give a clearly labelled general checklist; not an official exhaustive list."""
    service = str(service or "").strip().lower()[:100]
    common = ["Aadhaar or other accepted identity proof (if required)",
              "Address/residence proof (if required)",
              "Relevant application form and a working mobile number/email"]
    if any(x in service for x in ["scholarship", "student", "छात्र", "छात्रवृत्ति"]):
        items = common + ["Current academic/course and institution details", "Income/caste/disability certificate only if the selected scheme requires it", "Bank account details only through the official application portal"]
    elif any(x in service for x in ["farmer", "kisan", "किसान", "pm-kisan"]):
        items = common + ["Land/beneficiary records where required by the scheme", "Bank details only through the official portal"]
    elif any(x in service for x in ["health", "ayushman", "स्वास्थ्य"]):
        items = common + ["Check beneficiary eligibility and accepted documents on the official health scheme portal"]
    elif any(x in service for x in ["aadhaar", "document", "passport", "आधार", "दस्तावेज"]):
        items = common + ["Use the official service portal to confirm accepted proofs and appointment requirements"]
    else:
        items = common + ["Check the exact scheme/service page for its current mandatory documents"]
    return {"service": service, "general_checklist": items,
            "warning": "This is a general preparation checklist, not an official or exhaustive document list. Never share OTPs, passwords, UPI PINs or bank PINs with the assistant."}


AGENT_TOOLS = [
    {"type": "function", "function": {"name": "search_schemes", "description": "Search the AI JanSeva local catalogue for relevant Indian government schemes and public services.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "category": {"type": "string", "description": "Optional category such as Education, Healthcare, Farmers, Documents, Jobs, Women, Housing, Finance."}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_scheme_details", "description": "Look up one scheme in the local catalogue and return its description and official URL.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "document_checklist", "description": "Build a general preparation checklist for a scheme/service; clearly state that the official portal controls the final list.", "parameters": {"type": "object", "properties": {"service": {"type": "string"}}, "required": ["service"]}}}
]


def run_agent_tool(name, arguments):
    """Allowlist-only tool executor; model cannot run arbitrary code or URLs."""
    if not isinstance(arguments, dict):
        arguments = {}
    if name == "search_schemes":
        return janseva_search_schemes(arguments.get("query", ""), arguments.get("category", ""))
    if name == "get_scheme_details":
        return janseva_get_scheme_details(arguments.get("name", ""))
    if name == "document_checklist":
        return janseva_document_checklist(arguments.get("service", ""))
    return {"error": "Tool is not available."}





def scheme_application_guide(question):
    """Return a practical, cautious application guide for any of the 41 catalogue entries."""
    q = str(question or "").lower()
    action_words = [
        "apply", "application", "how to", "step by step", "steps", "process",
        "आवेदन", "अप्लाई", "कैसे करें", "प्रक्रिया", "फॉर्म भर", "register",
        "आवेदन कैसे", "कैसे apply", "कैसे आवेदन", "कदम", "participate", "eligibility", "requirements", "documents", "how can i get", "कैसे मिल", "पात्रता", "जरूरी दस्तावेज"
    ]
    # Recognise Beti Bachao Beti Padhao even when the user says only "help me with this scheme".
    if any(x in q for x in ["beti bachao beti padhao", "bbbp", "बेटी बचाओ", "বেটি বাঁচাও", "బేటీ బచావో", "பெண் குழந்தை"]):
        return {
            "title": "Beti Bachao Beti Padhao — scheme guidance",
            "official_url": "https://wcd.gov.in/",
            "steps": [
                "Open the Ministry of Women and Child Development official website and search for the current Beti Bachao Beti Padhao guidelines and notices.",
                "Understand that BBBP is primarily a programme to improve the value, protection and education of the girl child; it is not a universal direct-cash application scheme for every family.",
                "If you want to participate in local awareness or community activities, contact the Women and Child Development Department, District Programme Officer or relevant district administration and ask about current local activities.",
                "If you need financial assistance, scholarship or another individual benefit for a girl child, identify the separate central/state scheme and check its own eligibility and application process.",
                "Use only the official department or state portal for any application. Do not pay agents or share OTPs, passwords or bank PINs.",
                "Confirm current activities, eligibility and any available benefits with the official department; this guide does not confirm that an application window is open."
            ],
            "prepare": [
                "For general BBBP participation: no universal individual application document list; ask the district department about the activity.",
                "For a separate scholarship or benefit: prepare only the identity, residence, age, income or education documents required by that specific scheme."
            ],
            "important": "BBBP is not generally a direct cash benefit paid automatically to every girl or family. Verify any claim about money or applications with the official Women and Child Development Department."
        }

    # Disability Support is ambiguous: do not silently equate every benefit with UDID.
    if any(x in q for x in ["disability support", "disability benefit", "दिव्यांग सहायता", "दिव्यांग योजना"]):
        return {
            "title": "Disability Support — choose the service you need",
            "official_url": "https://swavlambancard.gov.in/",
            "steps": [
                "पहले तय करें कि आपको UDID/दिव्यांगता प्रमाणपत्र चाहिए या कोई अलग लाभ (पेंशन, छात्रवृत्ति, उपकरण, यात्रा रियायत आदि)। हर लाभ की प्रक्रिया अलग हो सकती है।",
                "यदि UDID कार्ड/दिव्यांगता प्रमाणपत्र चाहिए, तो आधिकारिक UDID पोर्टल https://swavlambancard.gov.in/ खोलें और वर्तमान आवेदन निर्देश पढ़ें।",
                "पोर्टल पर नया आवेदन/पंजीकरण विकल्प चुनें, आवेदक का विवरण भरें और निर्देशानुसार जिला/चिकित्सा प्राधिकरण चुनें।",
                "पोर्टल द्वारा मांगे गए पहचान/पता प्रमाण, फोटो और चिकित्सा/दिव्यांगता संबंधी रिकॉर्ड तैयार करें; केवल वही दस्तावेज़ अपलोड करें जो पोर्टल मांगे।",
                "आवेदन जमा करके acknowledgement/application number सुरक्षित रखें और पोर्टल पर स्थिति देखें। चिकित्सा मूल्यांकन या अतिरिक्त सत्यापन मांगा जाए तो उसे पूरा करें।",
                "यदि आपको पेंशन, छात्रवृत्ति, सहायक उपकरण या कोई अन्य लाभ चाहिए, तो उस लाभ का नाम और अपना राज्य बताएं; उसके लिए अलग आधिकारिक प्रक्रिया खोजनी होगी।"
            ],
            "prepare": [
                "UDID के लिए: पोर्टल द्वारा मांगे गए पहचान/पता प्रमाण, फोटो और संबंधित चिकित्सा रिकॉर्ड",
                "अन्य लाभों के लिए: संबंधित योजना की आधिकारिक सूची के अनुसार दस्तावेज़; सभी लाभों के लिए एक ही सूची लागू नहीं होती"
            ],
            "important": "Disability Support कोई एकल योजना नहीं है। यह मार्गदर्शिका UDID के रास्ते को बताती है, सभी दिव्यांग लाभों की पात्रता या आवेदन की पुष्टि नहीं करती। वर्तमान नियम आधिकारिक पोर्टल पर जांचें।"
        }

    # Route generic scholarship questions to NSP, but do not steal queries naming a
    # different scholarship such as Central Sector Scholarship or PM-YASASVI.
    named_scholarship = any(x in q for x in [
        "central sector scholarship", "css scholarship", "pm-yasasvi", "pm yasasvi", "yasasvi",
        "केंद्रीय क्षेत्र छात्रवृत्ति", "यशस्वी"
    ])
    if not named_scholarship and any(x in q for x in ["nsp", "national scholarship portal", "scholarship", "scholarships", "छात्रवृत्ति", "स्कॉलरशिप", "वजीफा"]):
        return {
            "title": "National Scholarship Portal (NSP) — आवेदन गाइड",
            "official_url": "https://scholarships.gov.in/",
            "steps": [
                "आधिकारिक NSP पोर्टल https://scholarships.gov.in/ खोलें और वर्तमान शैक्षणिक वर्ष की सूचनाएं व उपलब्ध योजनाएं देखें।",
                "योजना के दिशा-निर्देश पढ़ें और कोर्स, संस्थान, राज्य, श्रेणी, पारिवारिक आय तथा अन्य पात्रता शर्तें जांचें।",
                "यदि पोर्टल OTR (One Time Registration) मांगता है, तो वर्तमान निर्देशों के अनुसार अपना पंजीकरण पूरा करें।",
                "लॉग इन करके वही योजना चुनें जिसकी शर्तें आप पूरी करते हैं; आवेदन शुरू करने से पहले दस्तावेज़ सूची पढ़ें।",
                "व्यक्तिगत, शैक्षणिक, संस्थान और बैंक विवरण सही भरें; कोई जानकारी अनुमान से न भरें।",
                "केवल पोर्टल द्वारा मांगे गए दस्तावेज़ सही format/size में अपलोड करें।",
                "फॉर्म preview करें, जमा करें और acknowledgement/application number सुरक्षित रखें।",
                "पोर्टल पर status देखें और संस्था/विभाग द्वारा मांगे गए verification या correction को प्रदर्शित समय-सीमा के भीतर पूरा करें।"
            ],
            "prepare": [
                "कोर्स, वर्ष और संस्थान की जानकारी",
                "आय/श्रेणी/दिव्यांगता प्रमाणपत्र — केवल यदि चुनी गई योजना मांगती है",
                "बैंक विवरण — पोर्टल के निर्देशानुसार",
                "योजना के दिशा-निर्देशों में मांगे गए पहचान और संपर्क दस्तावेज़"
            ],
            "important": "यह सामान्य NSP प्रक्रिया है, पात्रता या आवेदन खुला होने की पुष्टि नहीं। OTR, दस्तावेज़ और समय-सीमा योजना/शैक्षणिक वर्ष के अनुसार बदल सकते हैं। OTP, पासवर्ड या बैंक PIN साझा न करें।"
        }

    # A named scheme is enough to trigger its guide; users should not have to phrase the question as "apply".

    # Match scheme names and useful aliases against all catalogue entries.
    aliases = {
        "PM-YASASVI": ["yasasvi", "pm yasasvi", "यशस्वी"],
        "Central Sector Scholarship": ["central sector scholarship", "css scholarship", "केंद्रीय क्षेत्र छात्रवृत्ति"],
        "Aadhaar Services": ["aadhaar", "aadhar", "आधार"],
        "DigiLocker": ["digilocker", "डिजिलॉकर", "download my documents", "download documents", "download document", "get my documents", "issued documents", "document download"],
        "Passport Seva": ["passport", "पासपोर्ट"],
        "Parivahan Sewa": ["parivahan", "driving licence", "driving license", "ड्राइविंग लाइसेंस"],
        "Ayushman Bharat PM-JAY": ["ayushman", "pm-jay", "आयुष्मान भारत"],
        "PM Matru Vandana Yojana": ["matru vandana", "pmmvy", "मातृ वंदना"],
        "PM-KISAN": ["pm kisan", "pm-kisan", "पीएम किसान"],
        "PM Fasal Bima Yojana": ["fasal bima", "crop insurance", "फसल बीमा"],
        "Kisan Credit Card": ["kisan credit card", "kcc", "किसान क्रेडिट कार्ड"],
        "PM Krishi Sinchayee Yojana": ["krishi sinchayee", "pmksy", "सिंचाई योजना"],
        "Soil Health Card": ["soil health", "मृदा स्वास्थ्य कार्ड"],
        "PMAY-Urban": ["pmay urban", "pmay-urban", "प्रधानमंत्री आवास शहरी"],
        "PMAY-Gramin": ["pmay gramin", "pmay-gramin", "प्रधानमंत्री आवास ग्रामीण"],
        "MGNREGA": ["mgnrega", "मनरेगा"],
        "PMKVY": ["pmkvy", "प्रधानमंत्री कौशल विकास"],
        "National Career Service": ["national career service", "ncs portal", "रोजगार सेवा"],
        "Pradhan Mantri Jan-Dhan Yojana": ["jan dhan", "जंधन", "जन धन"],
        "PM Jeevan Jyoti Bima Yojana": ["jeevan jyoti", "pmjjby", "जीवन ज्योति"],
        "PM Suraksha Bima Yojana": ["suraksha bima", "pmsby", "सुरक्षा बीमा"],
        "Atal Pension Yojana": ["atal pension", "apy", "अटल पेंशन"],
        "National Social Assistance Programme": ["nsap", "social assistance", "वृद्धावस्था पेंशन", "सामाजिक सहायता"],
        "Pradhan Mantri MUDRA Yojana": ["mudra", "मुद्रा लोन", "मुद्रा योजना"],
        "MSME Support": ["msme", "udyam", "उद्यम रजिस्ट्रेशन"],
        "PM Surya Ghar": ["surya ghar", "solar rooftop", "rooftop solar", "rooftop solar subsidy", "solar subsidy", "solar panel subsidy", "सूर्य घर", "सोलर रूफटॉप", "सोलर सब्सिडी"],
        "National Food Security": ["ration card", "food security", "nfsa", "राशन कार्ड", "खाद्य सुरक्षा"],
        "Disability Support": ["disability", "udid", "दिव्यांग", "दिव्यांगता"],
    }
    matched = None
    # Prefer an exact catalogue name before shorter aliases. Otherwise, for example,
    # "Ayushman Arogya Mandirs" was incorrectly captured by the shorter "ayushman" alias
    # for Ayushman Bharat PM-JAY.
    for record in sorted(SCHEMES, key=lambda item: len(item[0]), reverse=True):
        if record[0].lower() in q:
            matched = record
            break
    if matched is None:
        for record in SCHEMES:
            name, category, description, url, audience = record
            if any(alias.lower() in q for alias in aliases.get(name, []) if alias):
                matched = record
                break
    if not matched:
        return None

    name, category, description, url, audience = matched
    # These are category-appropriate preparation hints, not asserted mandatory documents.
    docs_by_category = {
        "Education": ["Course/year and institution details", "Academic marksheets, if requested", "Income/category certificate only if the selected scholarship requires it", "Bank details and identity documents only as listed in the current guidelines"],
        "Documents": ["Existing identity/contact details relevant to the service", "Proofs and photographs only if the official service asks for them", "Application/reference number for tracking"],
        "Healthcare": ["Identity and family/beneficiary details as requested", "Existing health/eligibility card or records, if applicable", "Medical or maternity records only if the scheme/portal asks for them"],
        "Farmers": ["Farmer and land/crop details relevant to the service", "Bank and identity details only as required", "Land records, crop details or insurance particulars if the portal/lender asks for them"],
        "Housing": ["Household and residence details", "Income/household or housing-related evidence if the scheme requires it", "Identity and bank details only as listed in the official rules"],
        "Jobs": ["Identity/contact details", "Education and skill certificates if applicable", "Bank details only where required by a specific benefit"],
        "Women": ["Beneficiary/guardian and household details as relevant", "Birth, pregnancy, nutrition or protection-related records only if the specific programme asks for them"],
        "Finance": ["Identity and contact details", "Bank account details as required by the bank/official scheme", "Age, nominee or consent information if required by the product"],
        "Business": ["Business/activity details", "Identity, address and bank records requested by the lender or portal", "Business plan/registration proof only if required by the selected programme"],
        "Digital": ["Service-specific household/address or beneficiary details", "Identity/contact details if required", "Any service-specific reference number or documents listed on the portal"],
    }
    docs = docs_by_category.get(category, ["Identity/contact details and service-specific records listed on the official portal"])
    steps = [
        f"Open the official portal listed for {name}: {url}.",
        f"Find the {name} section and read the current official guidelines, who can apply, and whether applications are currently accepted.",
        "Check all eligibility conditions that apply to you (for example state, age, income, course, occupation, household or beneficiary category). Do not assume eligibility from the scheme name alone.",
        "Use the portal's current instructions to choose online application, registration, bank/lender, local office or service-centre route as applicable; not every programme is a direct online benefit form.",
        "Prepare the documents explicitly listed in that scheme's current instructions. The checklist below is only a preparation aid, not an official mandatory list.",
        "Fill details accurately, review the form, upload only requested documents, and submit or complete the instructed in-person/bank verification step.",
        "Save the acknowledgement/reference number or receipt. If the service does not issue one online, note the official office/service-centre details.",
        "Track the request using the official portal or contact channel and complete any verification/correction requested by the department."
    ]
    # Better specific process notes for common services.
    if name == "DigiLocker":
        steps = [
            "Open https://www.digilocker.gov.in/ and select Sign Up or Sign In.",
            "Follow the portal's current mobile/identity verification steps; never share OTPs with another person.",
            "Set up your account and sign in.",
            "Use Issued Documents to fetch available government-issued documents, or Upload Documents for personal files where appropriate.",
            "Check the issuing authority and document details, then share/download only as needed."
        ]
        docs = ["Mobile number accessible to you", "Identity details required by the current sign-up process"]
    elif name == "Aadhaar Services":
        steps = [
            "Open https://uidai.gov.in/ and choose the exact service (enrolment, demographic update, document update, PVC card, or status check).",
            "Read whether the selected service is available online or requires an Aadhaar Seva Kendra/authorised centre appointment.",
            "Prepare the proof documents listed for that specific update; accepted documents vary by field and service.",
            "Complete the online request or visit the authorised centre and follow its identity-verification steps.",
            "Save the acknowledgement/URN/SRN if issued and use the official status service to track it."
        ]
        docs = ["Aadhaar number/details as relevant to the service", "Proof documents accepted for the particular update, as listed by UIDAI"]
    elif name == "Passport Seva":
        steps = [
            "Open https://www.passportindia.gov.in/ and register or sign in.",
            "Choose the correct service (fresh passport, re-issue or another service) and read the document adviser.",
            "Complete the application and pay/book an appointment if the portal requires it.",
            "Attend the Passport Seva Kendra/authorised centre with originals and copies listed in your appointment instructions.",
            "Complete police verification if required and track the application using the official reference number."
        ]
        docs = ["Documents shown by the official Passport Seva document adviser for your case", "Appointment/application reference and originals requested"]
    elif name == "Parivahan Sewa":
        steps = [
            "Open https://parivahan.gov.in/ and select the relevant state and service (learner licence, driving licence, vehicle service, etc.).",
            "Read service-specific eligibility and document instructions; requirements vary by state and service.",
            "Fill the online form and upload the requested proofs.",
            "Pay the displayed official fee if applicable and book a test/appointment where required.",
            "Complete any required in-person test or verification, then track/download the result through the official service."
        ]
        docs = ["Age/address proof and other documents requested for the selected service", "Existing licence/vehicle details if the service requires them"]
    elif name == "PM-KISAN":
        steps = [
            "Open https://pmkisan.gov.in/ and read the current beneficiary eligibility and exclusion rules.",
            "Use the official New Farmer Registration option if available, or ask the local agriculture office/authorised CSC for the current process.",
            "Enter farmer, land and bank details exactly as supported by official records.",
            "Complete any required e-KYC and land-record verification through official methods.",
            "Save the registration/reference details and check beneficiary/status pages for updates."
        ]
        docs = ["Landholding/land-record details", "Identity and bank details as required by the official registration process"]
    elif name == "PM Fasal Bima Yojana":
        steps = [
            "Open https://pmfby.gov.in/ and check whether your state, district, crop and season are notified.",
            "Read the current enrollment deadline, premium and eligibility rules for that crop-season; do not rely on old dates.",
            "Apply through the official portal or the currently authorised bank/CSC/channel described for your case.",
            "Provide accurate crop, land/tenancy and bank details and submit the documents required for that season.",
            "Save the receipt and follow official instructions for crop-loss reporting/claim deadlines if relevant."
        ]
        docs = ["Crop, season and land/tenancy details as required", "Bank and identity details requested by the authorised channel"]
    elif name == "Disability Support":
        steps = [
            "Clarify which service you need: UDID/disability certificate, pension, scholarship, assistive device or another benefit; they have different eligibility and application routes.",
            "For UDID/disability certificate specifically, open https://swavlambancard.gov.in/ and read the current application instructions.",
            "Choose the new application/registration option, enter applicant details, and select district/medical authority as directed.",
            "Prepare and upload only the identity, address, photo and medical records requested by the portal.",
            "Submit, save the acknowledgement number, and follow any medical assessment/document verification instructions.",
            "For a different disability benefit, check the relevant central/state department portal rather than assuming the UDID portal covers it."
        ]
        docs = ["For UDID: identity/address proof, photo and relevant medical records only as requested", "For other benefits: the selected benefit's official document list"]
    # Tailored workflows for every catalogue entry; these are navigation guides, not eligibility decisions.
    tailored = {
        "PM-YASASVI": ([
            "Open the official NTA YASASVI portal and check the latest notices for the current cycle.",
            "Confirm which examination/scholarship route is currently active and read the official eligibility, class, category and income conditions.",
            "Check whether registration, an entrance test, document verification or a separate scholarship portal is required for the current cycle.",
            "Register only through the official route, enter school/student details accurately, and complete any required exam or verification steps.",
            "Save the application number/admit card and monitor official notices for results, counselling or award instructions."
        ], ["Student and school details", "Category/income/academic documents only as required in the current notice"], "The route and selection process can change by cycle; follow the latest NTA notice."),
        "Central Sector Scholarship": ([
            "Open the National Scholarship Portal and locate the current Central Sector Scheme of Scholarship for College and University Students notice.",
            "Read the current rules for Class XII results, course, institution, family income, renewal and exclusions.",
            "Complete the portal's required registration/OTR and select the exact scheme only if the published rules fit your case.",
            "Enter academic, institution and bank details, upload requested proofs, and submit before the current deadline.",
            "Save the application ID and follow institute verification, correction and renewal instructions."
        ], ["Class XII marks and current course/institution details", "Income and bank/identity proofs only as required by the current scheme"], "Do not assume every college student qualifies; check current cut-offs, exclusions and deadlines."),
        "Samagra Shiksha": ([
            "Open the Ministry of Education's Samagra Shiksha page and read the programme information for your state and school level.",
            "Identify the service you need: school support, inclusive education, transport/hostel support or another state-implemented activity.",
            "Contact your school head, Block/District Education Office or state education department to ask how beneficiaries are identified locally.",
            "Follow the state/district instructions and provide only records requested for that specific service.",
            "Keep the school/office acknowledgement and follow up through the responsible education office."
        ], ["Student/school details", "Disability or other supporting records only if relevant to the requested service"], "Samagra Shiksha is a broad education programme, not one universal direct online application."),
        "Ayushman Bharat PM-JAY": ([
            "Open the official PM-JAY portal and use its beneficiary eligibility/check option or the currently linked official beneficiary service.",
            "Check whether the family appears in the eligible beneficiary database; eligibility is not based only on income or applying online.",
            "If listed, follow the official instructions to verify identity and obtain/activate the Ayushman card through an authorised channel.",
            "Choose a participating empanelled hospital and ask its Ayushman help desk to confirm covered treatment and pre-authorisation requirements.",
            "Keep the card/beneficiary details and hospital records; use official grievance channels if a problem occurs."
        ], ["Beneficiary/family identification details required by the official checker", "Identity proof and records requested by the authorised card/ hospital process"], "Coverage and eligibility depend on official beneficiary records and current programme rules."),
        "Ayushman Arogya Mandirs": ([
            "Use the official health department information to identify the nearest operational Ayushman Arogya Mandir/Health and Wellness Centre.",
            "Contact or visit the centre during its service hours and ask which primary-care services are available.",
            "Bring relevant health records and any identity/health card you already have; ask the centre what is needed for the requested service.",
            "For screening, consultation, medicines or referral, follow the health worker's directions.",
            "For emergencies or services not available there, use the appropriate public health facility/referral pathway."
        ], ["Existing health records and medicines list, if available", "Health/identity card if requested by the centre"], "This is a primary healthcare service network, not a single scheme application form."),
        "Mission Indradhanush": ([
            "Check the Ministry of Health or local health department notices for the current immunisation schedule and campaign dates in your area.",
            "Contact the nearest government health centre, ASHA or ANM to check which vaccinations are due for the child or pregnant person.",
            "Carry the available immunisation/Mother and Child Protection card and discuss any missed doses with the health worker.",
            "Attend the session advised by the health worker and keep the vaccination record updated.",
            "Ask the health centre about follow-up doses and local session dates."
        ], ["Immunisation/MCP card if available", "Child/pregnancy health records if available"], "Vaccination schedule and session dates should be confirmed with the local health authority."),
        "PM Matru Vandana Yojana": ([
            "Open the official PMMVY portal and read the current eligibility, benefit conditions and application instructions.",
            "Ask the local Anganwadi Worker/ASHA or designated health facility which registration channel and timeline currently apply.",
            "Complete the beneficiary registration with accurate pregnancy/childbirth and bank details as required by the portal.",
            "Submit only the documents required for the applicable benefit instalment and complete any health-service/registration conditions.",
            "Keep the acknowledgement and check status through the official channel; correct any mismatch requested by the department."
        ], ["Beneficiary and bank details as required", "Pregnancy/childbirth or MCP/health records only as listed in current PMMVY instructions"], "Eligibility, instalments and exclusions depend on current rules; verify locally and on the official portal."),
        "Kisan Credit Card": ([
            "Ask your bank or authorised cooperative bank about its current Kisan Credit Card application route; use MyScheme to review general scheme information.",
            "Explain the farming activity and credit purpose, and ask the lender for its current eligibility, limit and repayment terms.",
            "Complete the lender's form with accurate land/cropping or allied-activity details.",
            "Submit the identity, land/lease and other records requested by that lender; requirements vary by applicant and bank.",
            "Review interest, repayment, renewal and insurance terms before accepting the facility; keep the sanction and account documents."
        ], ["Land/cultivation or eligible allied-activity records as requested", "Identity/address and bank records required by the lender"], "KCC is a bank credit facility; approval and limit are decided by the lender, not guaranteed by the portal."),
        "PM Krishi Sinchayee Yojana": ([
            "Open the official PMKSY portal and identify the component relevant to you, such as micro-irrigation or a state-implemented water-management activity.",
            "Check your state's agriculture/irrigation department notice for the current component, beneficiary conditions, subsidy and application window.",
            "Contact the designated state/district agriculture or horticulture office to confirm whether application is online or through an approved service provider.",
            "Submit the farm, land, crop and equipment/project details requested by that component before purchasing or installing anything if pre-approval is required.",
            "Keep the receipt and follow inspection, installation, subsidy-claim or completion instructions from the department."
        ], ["Land/farm and crop details", "Quotation or technical/project details only if required by the selected component"], "PMKSY has multiple components; state implementation and subsidy rules differ."),
        "Soil Health Card": ([
            "Open the Soil Health Card portal for information and use the local agriculture department/soil-testing laboratory route available in your area.",
            "Contact the agriculture extension officer or authorised soil-testing laboratory to ask how to submit a field soil sample.",
            "Follow the laboratory's sampling instructions for the correct field and sample depth; label the sample as directed.",
            "Provide the farm/field details requested and submit the sample through the official channel.",
            "When the report/card is issued, review the nutrient recommendations with an agriculture officer before applying fertiliser."
        ], ["Farm/field location and crop details", "Sample container and field information as directed by the laboratory"], "Sampling method and availability vary locally; use the laboratory's instructions."),
        "PMAY-Urban": ([
            "Open the official PMAY-Urban portal and check the current mission phase, state/city instructions and eligible beneficiary category.",
            "Read the current conditions for the relevant vertical/benefit and confirm whether your household/property situation qualifies.",
            "Use the application route currently specified by the state/urban local body or official portal; do not rely on old forms or agents.",
            "Provide household, residence, income and property details accurately, with only the documents requested by the current guidelines.",
            "Save the application/acknowledgement and follow urban local body verification and status updates."
        ], ["Household and residence details", "Income, identity, property or bank records only as required by the current PMAY-U component"], "Mission phases, categories and application availability can change; confirm with the urban local body."),
        "PMAY-Gramin": ([
            "Check the official PMAY-G portal and contact your Gram Panchayat/Block Development Office about the current beneficiary list and process.",
            "Ask how the current rural housing eligibility and survey/list verification applies to your household; an online self-application may not be the route.",
            "If your household details are missing or incorrect, ask the Gram Panchayat/Block office about the official correction or grievance process.",
            "Provide household and identity details and any supporting records requested by the official verification process.",
            "Keep the complaint/receipt number and follow up with the Block or district rural development office."
        ], ["Household and residence details", "Supporting records requested by the Gram Panchayat/Block office"], "Beneficiary selection is governed by official rural housing criteria and lists; do not pay anyone to add a name."),
        "MGNREGA": ([
            "Contact your Gram Panchayat and request a Job Card or check the status of an existing card under the current MGNREGA process.",
            "Provide household member details and the information/documents requested by the Gram Panchayat; follow the official verification process.",
            "Once registered, submit a dated demand for work through the authorised local process and obtain an acknowledgement where available.",
            "Keep the Job Card and work-demand details; ask the Gram Panchayat about work allocation and the applicable timeline.",
            "Check muster roll, attendance and wage-payment status through official records; raise a grievance if work or payment is not recorded correctly."
        ], ["Household/member details requested for Job Card registration", "Existing Job Card and work-demand acknowledgement if already registered"], "Registration, work demand and wage rules are governed by the current state and MGNREGA procedures."),
        "PMKVY": ([
            "Open the official Skill India/PMKVY portal and check the currently active training programmes and authorised training centres.",
            "Choose a course that matches your age, education, location and career goal; read the course-specific eligibility and fee conditions.",
            "Contact the listed training centre to confirm that the batch is active and that the centre/course is authorised.",
            "Register through the official route and provide the requested learner details and documents.",
            "Attend training and assessment as prescribed, then check certification and placement-support details with the centre."
        ], ["Identity/contact and education details requested for the selected course", "Prior qualification proof if the course requires it"], "Course availability and scheme phases change; confirm the centre and batch through official channels."),
        "Skill India": ([
            "Open the official Skill India portal and search for courses, training centres or skill programmes currently listed.",
            "Compare course eligibility, duration, location, assessment and any fee before choosing.",
            "Contact the listed provider or official help channel to confirm the batch and registration method.",
            "Complete registration and provide only the learner documents requested for that course.",
            "Keep enrolment details and confirm assessment, certification and any placement support with the provider."
        ], ["Contact and education details", "Qualification or identity proof if required by the chosen course"], "Skill India is a programme ecosystem; individual courses have different providers and rules."),
        "Mission Shakti": ([
            "Open the Women and Child Development Ministry/state department website and identify the specific service under Mission Shakti that you need.",
            "For immediate danger, contact local emergency services/police; for support services, ask the official One Stop Centre or Women Helpline channel available in your state.",
            "Contact the district Women and Child Development office/One Stop Centre to confirm service availability, confidentiality and referral steps.",
            "Explain the type of support needed and provide only the information/documents the authorised service requires.",
            "Follow the caseworker's referral or support plan and keep official contact/reference details."
        ], ["No universal document list; bring relevant identity or case records only if safe and requested"], "Mission Shakti includes multiple services; access routes and helpline arrangements vary by state."),
        "Mission Vatsalya": ([
            "Open the Women and Child Development Ministry/state department page and identify the relevant child-protection service.",
            "For a child in immediate danger, contact emergency services or the Child Helpline/authorised child-protection authority available in your area.",
            "Contact the District Child Protection Unit (DCPU), Child Welfare Committee or district child-protection office for the appropriate referral.",
            "Follow the authorised officer's safeguarding and case-assessment process; do not publish a child's private details.",
            "Keep the official case/reference details and follow the responsible authority's directions."
        ], ["No universal document list; provide relevant child/family records only to authorised officials when requested"], "Child-protection cases should be handled by authorised agencies; protect the child's privacy."),
        "POSHAN Abhiyaan": ([
            "Open the official POSHAN portal or contact your local Anganwadi Centre to learn which nutrition services are available.",
            "Ask the Anganwadi Worker/ANM about registration and services for the relevant beneficiary group, such as children, pregnant women or lactating mothers.",
            "Provide beneficiary and household details requested for the local service and attend growth monitoring, counselling or nutrition sessions as advised.",
            "Keep any Mother and Child Protection card or nutrition/health record updated as directed.",
            "For missed services or eligibility questions, contact the supervisor or Block Women and Child Development office."
        ], ["Beneficiary/household details", "MCP or child growth/health records if available and requested"], "POSHAN is a multi-service programme; the local Anganwadi team can confirm services and records."),
        "Pradhan Mantri Jan-Dhan Yojana": ([
            "Visit a participating bank branch or use the bank's official channel and ask about opening a basic savings account under PMJDY.",
            "Read the bank's current account-opening and KYC instructions, including available simplified-KYC options if applicable.",
            "Complete the bank form and provide accepted identity/address or other KYC documents requested by the bank.",
            "Review account terms, debit card availability and optional services before consenting.",
            "Keep the account details secure and use only official bank channels for account support."
        ], ["KYC documents accepted by the chosen bank", "Mobile/contact details requested by the bank"], "Account opening is handled by banks and subject to current KYC rules; never share PIN or OTP."),
        "PM Jeevan Jyoti Bima Yojana": ([
            "Read the current PMJJBY rules on the Jan Suraksha portal and confirm age, premium, cover and renewal conditions.",
            "Contact your participating bank/post office or use its official channel to check enrolment availability and linked-account requirements.",
            "Read the consent/auto-debit and nominee terms before opting in.",
            "Submit the enrolment/consent form through the authorised institution and keep confirmation.",
            "Check annual renewal, premium debit and claim procedure with the bank/insurer; keep nominee details updated."
        ], ["Savings account details and nominee information as requested", "Consent/enrolment details required by the participating institution"], "Premium, age limits and terms can change; verify current official rules before enrolling."),
        "PM Suraksha Bima Yojana": ([
            "Read the current PMSBY rules on the Jan Suraksha portal, including age range, premium, coverage and exclusions.",
            "Contact your participating bank/post office or its official digital channel about enrolment.",
            "Review the accident-cover terms, linked-account requirement and auto-debit consent.",
            "Submit the authorised enrolment/consent and save confirmation.",
            "For a claim, contact the bank/insurer and follow the current claim form and deadline instructions."
        ], ["Linked bank account details", "Nominee and claim documents only as requested by the bank/insurer"], "Coverage applies only under policy terms and exclusions; verify the current policy and claim deadlines."),
        "Atal Pension Yojana": ([
            "Read the current APY eligibility and contribution information from the official pension authority and participating bank.",
            "Confirm age eligibility, savings-account requirement, contribution amount and pension option before enrolling.",
            "Apply through your bank or its official digital channel and complete the required consent/mandate.",
            "Check that the chosen contribution and pension details are correct and keep the enrolment acknowledgement.",
            "Monitor contributions and update contact/nominee details through the bank's official process."
        ], ["Savings account and KYC details requested by the bank", "Nominee and contribution/mandate details"], "Eligibility and contribution rules should be checked against the current official APY guidance."),
        "National Career Service": ([
            "Open https://www.ncs.gov.in/ and create an account or sign in using the current official registration process.",
            "Complete your jobseeker profile with accurate education, skills, experience, preferred location and contact details.",
            "Search vacancies by role, location, qualification and experience; read each employer's requirements before applying.",
            "Apply through the portal's listed process and keep track of applications, messages and interview details.",
            "Use NCS career counselling or job-fair information where available, and report suspicious requests for payment through official channels."
        ], ["Accurate contact details", "Education/skill and experience information", "Resume and certificates if requested by an employer"], "NCS lists employment and career services; it does not guarantee a job. Do not pay recruiters for a promised job."),
        "National Social Assistance Programme": ([
            "Open the NSAP portal for programme information, then contact your Gram Panchayat/municipality or state social-welfare office for the applicable pension route.",
            "Identify the relevant pension/assistance category and check the current age, income, disability or household conditions for your state.",
            "Ask the local office for the current application form and whether submission is online or in person.",
            "Submit the form and only the identity, residence, income, age or disability records required by the applicable programme.",
            "Keep the receipt and follow up through the local/state portal for verification and payment status."
        ], ["Age/residence and beneficiary details", "Income, disability or other supporting records only if required by the applicable pension"], "NSAP components and state top-ups differ; confirm the state-specific eligibility and application route."),
        "Startup India": ([
            "Open the Startup India portal and read the current startup recognition criteria and available support programmes.",
            "If seeking DPIIT recognition, confirm that the entity type, age and innovation/scale criteria meet the current rules.",
            "Create an account and follow the current recognition/application workflow shown on the portal.",
            "Provide entity incorporation/registration details and declarations/documents specifically requested in the form.",
            "Save the application reference and monitor portal messages; apply separately to any incubator, challenge or funding programme."
        ], ["Entity incorporation/registration details", "Business and founder information and supporting declarations requested by the portal"], "Recognition does not automatically grant funding or every benefit; each programme has separate criteria."),
        "Pradhan Mantri MUDRA Yojana": ([
            "Review MUDRA loan information and approach a participating bank, NBFC or other authorised lending institution; MUDRA itself is not a universal direct-grant application.",
            "Choose the loan purpose and ask the lender about current product category, eligibility, interest, margin and repayment terms.",
            "Prepare a realistic business/project plan and estimate the amount needed.",
            "Submit the lender's application and the identity, address, business, bank and financial records requested for your case.",
            "Review the sanction letter and repayment obligations before accepting; keep all lender receipts and loan documents."
        ], ["Business/project details and estimated loan requirement", "Identity, address, business and financial documents requested by the lender"], "Loan approval, amount, interest and collateral conditions are decided by the lender; funding is not guaranteed."),
        "MSME Support": ([
            "Open the Ministry of MSME website and identify the exact service you need, such as Udyam registration, training, market access, credit support or grievance help.",
            "For Udyam registration, use only the official Udyam portal linked from the ministry and read the current eligibility/instructions.",
            "For other support, check the relevant scheme notice, application window and implementing agency; each programme has its own form.",
            "Enter business details accurately and submit only the records requested by that service.",
            "Save the registration/receipt and track through the official ministry, agency or portal."
        ], ["Business/activity and proprietor/entity details", "PAN/GST/bank or other records only as required for the selected service"], "MSME Support is a broad category, not one scheme; avoid unofficial paid registration agents."),
        "Digital India": ([
            "Open the Digital India portal and identify the specific service or initiative you want to use.",
            "Check whether it is an information programme, public digital service, training opportunity or separate scheme with its own eligibility.",
            "Follow the official linked department/portal for registration or service access; do not treat the umbrella initiative as one application.",
            "Provide only details required by the specific service and keep any reference number.",
            "For help, use the official department contact linked from the Digital India portal."
        ], ["Documents depend entirely on the specific linked service; check that service's official instructions"], "Digital India is an umbrella initiative and has no single universal beneficiary application."),
        "Swachh Bharat Mission": ([
            "Open the official Swachh Bharat Mission portal and determine whether your query concerns rural sanitation, urban sanitation, a local service or a programme benefit.",
            "For household toilet or local sanitation assistance, contact the Gram Panchayat/rural development office or urban local body for the current state process.",
            "Ask the local authority about beneficiary eligibility, verification and whether any application window is active.",
            "Submit household/location details and supporting records only as requested by the relevant local scheme.",
            "Keep the acknowledgement and follow up with the responsible local body."
        ], ["Household/location details", "Identity or household records only if requested by the local authority"], "Rural and urban components are implemented differently; use the relevant local authority."),
        "Jal Jeevan Mission": ([
            "Open the Jal Jeevan Mission portal for programme information and contact your Gram Panchayat/Village Water and Sanitation Committee or state water department about local service.",
            "If reporting a household tap-water issue, use the state/district complaint mechanism linked by the official department.",
            "Provide the village/household location and a clear description of the supply problem; do not post sensitive personal information publicly.",
            "Save the complaint number if issued and follow up with the local water department.",
            "For a new connection or local project query, confirm the process with the state/Gram Panchayat because delivery is locally implemented."
        ], ["Village/household location and complaint details", "Connection/account reference if applicable"], "JJM is primarily a public water-supply mission, not a single national individual cash-benefit form."),
        "PM Surya Ghar": ([
            "Open https://pmsuryaghar.gov.in/ and read the current residential rooftop-solar eligibility and subsidy instructions.",
            "Register using the consumer details requested and select the correct electricity distribution company (DISCOM) and consumer account.",
            "Follow the portal's current process for vendor selection and technical/feasibility approval before installation.",
            "Use an eligible/registered vendor as required, complete installation and arrange the required inspection/net-metering steps.",
            "Submit the commissioning/subsidy request through the portal, enter bank details carefully and track its status."
        ], ["Electricity consumer/account number and service details", "Bank details and installation/commissioning records requested by the portal"], "Subsidy depends on current rules and successful portal, DISCOM and installation steps; verify before paying a vendor."),
        "National Food Security": ([
            "Open the NFSA portal for policy information and use your state food/civil supplies department for ration-card applications and corrections.",
            "Check the state-specific eligibility and whether you need a new ration card, member addition, correction, portability or grievance service.",
            "Use the official state portal or designated local office/CSC route described by the state.",
            "Provide household/member, residence and identity information and only the supporting documents the state requires.",
            "Save the receipt and track verification/status with the state department; report any demand for unofficial payment."
        ], ["Household/member and residence details", "Identity and income/category records only as required by the state process"], "Ration-card eligibility and application procedures are state-specific; NFSA is not one uniform national form."),
    }
    if name in tailored:
        steps, docs, tailored_caution = tailored[name]
        important = tailored_caution
    else:
        important = f"{description} यह मार्गदर्शन {name} के लिए सामान्य navigation help है; यह live eligibility, आवेदन खुला होने, benefit approval या deadline की पुष्टि नहीं करता। वर्तमान पात्रता, documents, fees और समय-सीमा आधिकारिक portal पर जांचें।"

    return {
        "title": f"{name} — आवेदन मार्गदर्शिका",
        "official_url": url,
        "category": category,
        "steps": steps,
        "prepare": docs,
        "important": important
    }

def format_application_guide(guide, language="en"):
    """Format grounded application guidance in the selected website language."""
    labels = {
        "en": ("Official portal:", "Step-by-step:", "Documents to prepare (confirm exact list on portal):", "Important:"),
        "hi": ("आधिकारिक पोर्टल:", "आवेदन के चरण:", "तैयार रखने वाले दस्तावेज़ (सही सूची पोर्टल पर जाँचें):", "महत्वपूर्ण:"),
        "bn": ("সরকারি পোর্টাল:", "আবেদনের ধাপ:", "প্রস্তুত রাখার নথি (সঠিক তালিকা পোর্টালে যাচাই করুন):", "গুরুত্বপূর্ণ:"),
        "te": ("అధికారిక పోర్టల్:", "దరఖాస్తు దశలు:", "సిద్ధం చేసుకోవాల్సిన పత్రాలు (ఖచ్చితమైన జాబితాను పోర్టల్‌లో తనిఖీ చేయండి):", "ముఖ్యమైనది:"),
        "ta": ("அதிகாரப்பூர்வ இணையதளம்:", "விண்ணப்பிக்கும் படிகள்:", "தயாராக வைத்திருக்க வேண்டிய ஆவணங்கள் (சரியான பட்டியலை இணையதளத்தில் சரிபார்க்கவும்):", "முக்கியம்:"),
        "mr": ("अधिकृत पोर्टल:", "अर्ज करण्याच्या पायऱ्या:", "तयार ठेवायची कागदपत्रे (अचूक यादी पोर्टलवर तपासा):", "महत्त्वाचे:"),
    }
    language = language if language in labels else "en"
    portal_label, steps_label, docs_label, important_label = labels[language]
    title, steps, docs, important = guide["title"], list(guide["steps"]), list(guide["prepare"]), guide["important"]
    # Explicit translations for common user tasks shown in the UI.
    if "DigiLocker" in title and language == "hi":
        title = "DigiLocker — डिजिटल दस्तावेज़ डाउनलोड गाइड"
        steps = [
            "आधिकारिक वेबसाइट https://www.digilocker.gov.in/ खोलें।",
            "अपने खाते में साइन इन करें। नया खाता हो तो आधिकारिक निर्देशों के अनुसार पंजीकरण पूरा करें।",
            "Issued Documents (जारी दस्तावेज़) अनुभाग खोलें और उपलब्ध दस्तावेज़ों में अपना दस्तावेज़ खोजें।",
            "दस्तावेज़ खोलें और यदि उपलब्ध हो तो Download/Save विकल्प चुनें।",
            "यदि दस्तावेज़ नहीं दिख रहा है, तो सही issuer/विभाग चुनकर दोबारा जाँचें; कुछ दस्तावेज़ पहले जारीकर्ता से fetch करने पड़ते हैं।",
            "डाउनलोड की गई फ़ाइल सुरक्षित रखें। OTP, पासवर्ड या PIN किसी से साझा न करें।"
        ]
        docs = ["DigiLocker खाते से जुड़ा मोबाइल नंबर/साइन-इन विवरण", "यदि मांगा जाए तो दस्तावेज़ खोजने के लिए संबंधित जारीकर्ता या दस्तावेज़ का विवरण"]
        important = "सभी दस्तावेज़ हर खाते में अपने-आप उपलब्ध नहीं होते। केवल आधिकारिक DigiLocker वेबसाइट/ऐप का उपयोग करें।"
    elif "DigiLocker" in title and language == "bn":
        title = "DigiLocker — ডিজিটাল নথি ডাউনলোড নির্দেশিকা"
        steps = [
            "সরকারি ওয়েবসাইট https://www.digilocker.gov.in/ খুলুন।",
            "আপনার অ্যাকাউন্টে সাইন ইন করুন। নতুন অ্যাকাউন্ট হলে সরকারি নির্দেশ অনুযায়ী নিবন্ধন করুন।",
            "Issued Documents বিভাগ খুলে আপনার উপলব্ধ নথিটি খুঁজুন।",
            "নথিটি খুলে Download/Save বিকল্প থাকলে সেটি ব্যবহার করুন।",
            "নথি না দেখালে সঠিক issuer/বিভাগ নির্বাচন করে আবার দেখুন; কিছু নথি আগে সংশ্লিষ্ট সংস্থা থেকে আনতে হয়।",
            "ডাউনলোড করা ফাইল নিরাপদে রাখুন। OTP, পাসওয়ার্ড বা PIN কারও সঙ্গে ভাগ করবেন না।"
        ]
        docs = ["DigiLocker অ্যাকাউন্টে ব্যবহৃত মোবাইল/সাইন-ইন তথ্য", "নথি খুঁজতে প্রয়োজন হলে সংশ্লিষ্ট issuer বা নথির বিবরণ"]
        important = "সব নথি প্রতিটি অ্যাকাউন্টে স্বয়ংক্রিয়ভাবে থাকে না। শুধুমাত্র সরকারি DigiLocker ওয়েবসাইট/অ্যাপ ব্যবহার করুন।"
    elif "DigiLocker" in title and language == "en":
        title = "DigiLocker — Download Your Documents"
        steps = [
            "Open the official website https://www.digilocker.gov.in/.",
            "Sign in to your account. If you are new, complete registration using the official instructions.",
            "Open Issued Documents and find the document available in your account.",
            "Open the document and use Download/Save if the option is available.",
            "If it is missing, check the correct issuer/department; some documents must first be fetched from the issuing authority.",
            "Save the file securely. Never share your OTP, password or PIN."
        ]
        docs = ["The mobile/sign-in details linked to your DigiLocker account", "Issuer or document details if needed to locate the record"]
        important = "Not every document is automatically available in every account. Use only the official DigiLocker website/app."
    elif "PM Surya Ghar" in title and language == "hi":
        title = "PM Surya Ghar — रूफटॉप सोलर सब्सिडी गाइड"
        steps = [
            "आधिकारिक पोर्टल https://pmsuryaghar.gov.in/ खोलें और वर्तमान पात्रता तथा सब्सिडी नियम पढ़ें।",
            "निर्देशानुसार अपने राज्य, बिजली वितरण कंपनी (DISCOM) और उपभोक्ता/कनेक्शन विवरण के साथ पंजीकरण करें।",
            "पोर्टल पर उपलब्ध प्रक्रिया के अनुसार आवेदन जमा करें और आवश्यक तकनीकी/व्यवहार्यता स्वीकृति की प्रतीक्षा करें।",
            "जहाँ आवश्यक हो, पोर्टल पर सूचीबद्ध पात्र विक्रेता चुनें। इंस्टॉलेशन से पहले वर्तमान निर्देश जाँचें।",
            "इंस्टॉलेशन के बाद DISCOM निरीक्षण, नेट मीटरिंग और commissioning की आवश्यक प्रक्रिया पूरी करें।",
            "पोर्टल पर सब्सिडी अनुरोध जमा करें, सही बैंक विवरण दें और आवेदन की स्थिति ट्रैक करें।"
        ]
        docs = ["बिजली उपभोक्ता/कनेक्शन नंबर और DISCOM विवरण", "पोर्टल द्वारा मांगे गए बैंक विवरण और इंस्टॉलेशन/commissioning रिकॉर्ड"]
        important = "पात्रता, सब्सिडी राशि और प्रक्रिया वर्तमान नियमों पर निर्भर करती है। विक्रेता को भुगतान करने से पहले आधिकारिक पोर्टल और DISCOM के निर्देश जाँचें।"
    elif "PM Surya Ghar" in title and language == "bn":
        title = "PM Surya Ghar — ছাদের সৌরবিদ্যুৎ ভর্তুকি নির্দেশিকা"
        steps = [
            "সরকারি পোর্টাল https://pmsuryaghar.gov.in/ খুলে বর্তমান যোগ্যতা ও ভর্তুকির নিয়ম পড়ুন।",
            "নির্দেশ অনুযায়ী রাজ্য, বিদ্যুৎ বিতরণ সংস্থা (DISCOM) এবং গ্রাহক/সংযোগের তথ্য দিয়ে নিবন্ধন করুন।",
            "পোর্টালে দেখানো প্রক্রিয়া অনুসারে আবেদন জমা দিন এবং প্রয়োজনীয় প্রযুক্তিগত অনুমোদনের জন্য অপেক্ষা করুন।",
            "যেখানে প্রয়োজন, পোর্টালে তালিকাভুক্ত যোগ্য বিক্রেতা নির্বাচন করুন। ইনস্টলেশনের আগে বর্তমান নির্দেশ যাচাই করুন।",
            "ইনস্টলেশনের পরে DISCOM পরিদর্শন, নেট মিটারিং এবং commissioning-এর প্রয়োজনীয় ধাপ সম্পন্ন করুন।",
            "পোর্টালে ভর্তুকির আবেদন জমা দিন, ব্যাংকের তথ্য সঠিকভাবে দিন এবং আবেদনের অবস্থা দেখুন।"
        ]
        docs = ["বিদ্যুৎ গ্রাহক/সংযোগ নম্বর এবং DISCOM-এর তথ্য", "পোর্টালে চাওয়া ব্যাংকের তথ্য ও ইনস্টলেশন/commissioning-এর নথি"]
        important = "যোগ্যতা, ভর্তুকির পরিমাণ ও প্রক্রিয়া বর্তমান নিয়মের উপর নির্ভর করে। বিক্রেতাকে অর্থ দেওয়ার আগে সরকারি পোর্টাল ও DISCOM-এর নির্দেশ যাচাই করুন।"
    elif "PM Surya Ghar" in title and language == "en":
        title = "PM Surya Ghar — Rooftop Solar Subsidy Guide"
        steps = [
            "Open https://pmsuryaghar.gov.in/ and read the current eligibility and subsidy rules.",
            "Register with the state, electricity distribution company (DISCOM) and consumer/connection details requested by the portal.",
            "Submit the application through the current portal workflow and wait for any required technical/feasibility approval.",
            "Where required, choose an eligible vendor listed on the portal. Check the current instructions before installation or payment.",
            "After installation, complete the required DISCOM inspection, net-metering and commissioning steps.",
            "Submit the subsidy request through the portal, enter bank details carefully and track the application status."
        ]
        docs = ["Electricity consumer/connection number and DISCOM details", "Bank details and installation/commissioning records requested by the portal"]
        important = "Eligibility, subsidy amount and process depend on current rules. Verify instructions with the official portal and DISCOM before paying a vendor."
    if language == "hi" and "National Scholarship Portal" in title:
        title = "नेशनल स्कॉलरशिप पोर्टल (NSP) — आवेदन गाइड"
        steps = [
            "आधिकारिक पोर्टल https://scholarships.gov.in/ खोलें और वर्तमान शैक्षणिक वर्ष की सूचनाएँ व उपलब्ध योजनाएँ देखें।",
            "योजना के दिशा-निर्देश पढ़ें। कोर्स, संस्थान, राज्य, श्रेणी, पारिवारिक आय और अन्य पात्रता शर्तें जाँचें।",
            "यदि पोर्टल OTR (One Time Registration) माँगता है, तो मौजूदा निर्देशों के अनुसार अपना पंजीकरण पूरा करें।",
            "लॉग इन करके अपनी पात्रता के अनुसार योजना चुनें और आवश्यक दस्तावेज़ों की सूची पढ़ें।",
            "व्यक्तिगत, शैक्षणिक, संस्थान और बैंक विवरण सही-सही भरें।",
            "पोर्टल द्वारा माँगे गए दस्तावेज़ निर्देशों के अनुसार अपलोड करें।",
            "फॉर्म की समीक्षा करें, आवेदन जमा करें और आवेदन संख्या/रसीद सुरक्षित रखें।",
            "पोर्टल पर आवेदन की स्थिति देखें और समय-सीमा से पहले माँगे गए सुधार पूरे करें।"
        ]
        docs = ["कोर्स और संस्थान का विवरण", "आय/श्रेणी/दिव्यांगता प्रमाणपत्र—केवल यदि योजना माँगे", "बैंक विवरण—केवल पोर्टल के निर्देशानुसार", "योजना के दिशा-निर्देशों में बताए गए पहचान और संपर्क दस्तावेज़"]
        important = "यह सामान्य मार्गदर्शन है; इससे पात्रता या आवेदन खुला होने की पुष्टि नहीं होती। समय-सीमा और दस्तावेज़ आधिकारिक पोर्टल पर जाँचें। OTP, पासवर्ड या बैंक PIN साझा न करें।"
    elif language == "bn" and "National Scholarship Portal" in title:
        title = "ন্যাশনাল স্কলারশিপ পোর্টাল (NSP) — আবেদন নির্দেশিকা"
        steps = [
            "সরকারি পোর্টাল https://scholarships.gov.in/ খুলুন এবং বর্তমান শিক্ষাবর্ষের বিজ্ঞপ্তি ও উপলব্ধ বৃত্তি দেখুন।",
            "বৃত্তির নির্দেশিকা পড়ুন। কোর্স, প্রতিষ্ঠান, রাজ্য, শ্রেণি, পারিবারিক আয় এবং অন্যান্য যোগ্যতার শর্ত যাচাই করুন।",
            "পোর্টাল OTR (One Time Registration) চাইলে, বর্তমান নির্দেশ অনুযায়ী নিবন্ধন সম্পন্ন করুন।",
            "লগ ইন করে আপনার যোগ্যতার সঙ্গে মেলে এমন বৃত্তি বেছে নিন এবং নথির তালিকা পড়ুন।",
            "ব্যক্তিগত, শিক্ষাগত, প্রতিষ্ঠান ও ব্যাংকের তথ্য সঠিকভাবে পূরণ করুন।",
            "পোর্টালের নির্দেশ অনুযায়ী প্রয়োজনীয় নথি আপলোড করুন।",
            "ফর্ম যাচাই করে জমা দিন এবং আবেদন নম্বর/স্বীকৃতিপত্র সংরক্ষণ করুন।",
            "পোর্টালে আবেদনের অবস্থা দেখুন এবং সময়সীমার আগে সংশোধনের অনুরোধ পূরণ করুন।"
        ]
        docs = ["কোর্স ও প্রতিষ্ঠানের বিবরণ", "আয়/শ্রেণি/প্রতিবন্ধিতার শংসাপত্র—শুধু বৃত্তি চাইলে", "ব্যাংকের তথ্য—পোর্টালের নির্দেশ অনুযায়ী", "নির্দেশিকায় চাওয়া পরিচয় ও যোগাযোগের নথি"]
        important = "এটি সাধারণ নির্দেশিকা; যোগ্যতা বা আবেদন বর্তমানে খোলা থাকার নিশ্চয়তা নয়। সময়সীমা ও নথি সরকারি পোর্টালে যাচাই করুন। OTP, পাসওয়ার্ড বা ব্যাংক PIN কাউকে দেবেন না।"
    if "UDID / Disability Certificate" in title and language == "hi":
        title = "UDID / दिव्यांगता प्रमाणपत्र — आवेदन गाइड"
        steps = [
            "आधिकारिक UDID पोर्टल खोलें और पुष्टि करें कि आपको UDID कार्ड/दिव्यांगता प्रमाणपत्र चाहिए; अन्य सहायता योजनाओं के पोर्टल अलग हो सकते हैं।",
            "वर्तमान निर्देश पढ़ें और पोर्टल पर उपलब्ध नया आवेदन/पंजीकरण विकल्प चुनें।",
            "आवेदक की जानकारी सही भरें और निर्देशानुसार जिला/चिकित्सा प्राधिकरण चुनें।",
            "पोर्टल द्वारा माँगे गए पहचान, पते, फोटो और चिकित्सा/दिव्यांगता रिकॉर्ड तैयार करके अपलोड करें।",
            "आवेदन जमा करें और पावती/आवेदन संख्या सुरक्षित रखें।",
            "आवेदन की स्थिति देखें और माँगे जाने पर चिकित्सा मूल्यांकन या दस्तावेज़ सत्यापन पूरा करें।",
            "मंजूरी के बाद पोर्टल के उपलब्ध डाउनलोड/स्थिति विकल्प इस्तेमाल करें या आधिकारिक हेल्पडेस्क से संपर्क करें।"
        ]
        docs = ["पोर्टल पर बताए अनुसार पहचान और पते का प्रमाण", "यदि माँगा जाए तो फोटो और संपर्क विवरण", "पोर्टल द्वारा माँगे गए संबंधित चिकित्सा/दिव्यांगता रिकॉर्ड"]
        important = "यह गाइड UDID/दिव्यांगता प्रमाणपत्र के लिए है, हर दिव्यांग सहायता योजना के लिए नहीं। वर्तमान शर्तें आधिकारिक पोर्टल पर जाँचें।"
    elif "UDID / Disability Certificate" in title and language == "bn":
        title = "UDID / প্রতিবন্ধিতা শংসাপত্র — আবেদন নির্দেশিকা"
        steps = [
            "সরকারি UDID পোর্টাল খুলুন এবং নিশ্চিত করুন যে আপনার UDID কার্ড/প্রতিবন্ধিতা শংসাপত্রের পরিষেবা দরকার; অন্য সহায়তা প্রকল্পের পোর্টাল আলাদা হতে পারে।",
            "বর্তমান নির্দেশ পড়ে পোর্টালে থাকা নতুন আবেদন/নিবন্ধনের বিকল্প নির্বাচন করুন।",
            "আবেদনকারীর তথ্য সঠিকভাবে দিন এবং নির্দেশ অনুযায়ী জেলা/চিকিৎসা কর্তৃপক্ষ নির্বাচন করুন।",
            "পোর্টালে চাওয়া পরিচয়, ঠিকানা, ছবি ও চিকিৎসা/প্রতিবন্ধিতা সংক্রান্ত নথি প্রস্তুত করে আপলোড করুন।",
            "আবেদন জমা দিয়ে স্বীকৃতিপত্র/আবেদন নম্বর সংরক্ষণ করুন।",
            "আবেদনের অবস্থা দেখুন এবং চাইলে চিকিৎসা মূল্যায়ন বা নথি যাচাই সম্পন্ন করুন।",
            "অনুমোদনের পর পোর্টালের ডাউনলোড/স্ট্যাটাস বিকল্প ব্যবহার করুন অথবা সরকারি হেল্পডেস্কে যোগাযোগ করুন।"
        ]
        docs = ["পোর্টালে চাওয়া পরিচয় ও ঠিকানার প্রমাণ", "চাইলে ছবি ও যোগাযোগের তথ্য", "পোর্টালে চাওয়া চিকিৎসা/প্রতিবন্ধিতা সংক্রান্ত নথি"]
        important = "এই নির্দেশিকা UDID/প্রতিবন্ধিতা শংসাপত্রের জন্য, সব প্রতিবন্ধী সহায়তা প্রকল্পের জন্য নয়। বর্তমান শর্ত সরকারি পোর্টালে যাচাই করুন।"
    # Translate the disability/UDID guide for the selected UI language instead
    # of falling back to the English source strings.
    if "UDID / Disability Certificate" in title and language == "te":
        title = "UDID / వైకల్య ధృవీకరణ పత్రం — దరఖాస్తు మార్గదర్శిని"
        steps = [
            "అధికారిక UDID పోర్టల్‌ను తెరవండి. మీకు UDID కార్డు/వైకల్య ధృవీకరణ పత్రమే కావాలా నిర్ధారించుకోండి; ఇతర సహాయ పథకాల దరఖాస్తు విధానం వేరుగా ఉండవచ్చు.",
            "పోర్టల్‌లోని తాజా సూచనలను చదివి, కొత్త దరఖాస్తు/నమోదు ఎంపికను ఎంచుకోండి.",
            "దరఖాస్తుదారుడి వివరాలను ఖచ్చితంగా నమోదు చేసి, సూచనల ప్రకారం జిల్లా లేదా వైద్య అధికారిని ఎంచుకోండి.",
            "పోర్టల్ కోరిన గుర్తింపు, చిరునామా, ఫోటో మరియు సంబంధిత వైద్య/వైకల్య పత్రాలను సిద్ధం చేసి అప్‌లోడ్ చేయండి.",
            "దరఖాస్తును సమర్పించి, రసీదు లేదా దరఖాస్తు సంఖ్యను భద్రపరచండి.",
            "దరఖాస్తు స్థితిని తనిఖీ చేయండి. కోరితే వైద్య మూల్యాంకనం లేదా పత్రాల ధృవీకరణ పూర్తి చేయండి.",
            "ఆమోదం తర్వాత పోర్టల్‌లో అందుబాటులో ఉన్న డౌన్‌లోడ్/స్థితి ఎంపికలను ఉపయోగించండి లేదా అధికారిక సహాయ కేంద్రాన్ని సంప్రదించండి."
        ]
        docs = ["పోర్టల్ కోరిన గుర్తింపు మరియు చిరునామా రుజువు", "అడిగితే ఫోటో మరియు సంప్రదింపు వివరాలు", "పోర్టల్ కోరిన సంబంధిత వైద్య/వైకల్య పత్రాలు"]
        important = "ఈ మార్గదర్శిని UDID/వైకల్య ధృవీకరణ పత్రం కోసం మాత్రమే; అన్ని వైకల్య సహాయ పథకాలకు కాదు. తాజా నియమాలను అధికారిక పోర్టల్‌లో తనిఖీ చేయండి."
    elif "UDID / Disability Certificate" in title and language == "ta":
        title = "UDID / மாற்றுத்திறனாளர் சான்றிதழ் — விண்ணப்ப வழிகாட்டி"
        steps = [
            "அதிகாரப்பூர்வ UDID இணையதளத்தைத் திறந்து, உங்களுக்கு UDID அட்டை/மாற்றுத்திறனாளர் சான்றிதழ்தான் தேவையா என்பதை உறுதிப்படுத்தவும்; பிற உதவித் திட்டங்களுக்கு வேறு நடைமுறை இருக்கலாம்.",
            "இணையதளத்தின் தற்போதைய வழிமுறைகளைப் படித்து, புதிய விண்ணப்பம்/பதிவு விருப்பத்தைத் தேர்ந்தெடுக்கவும்.",
            "விண்ணப்பதாரர் விவரங்களைச் சரியாக நிரப்பி, அறிவுறுத்தலின்படி மாவட்டம்/மருத்துவ அதிகாரியைத் தேர்ந்தெடுக்கவும்.",
            "கேட்கப்பட்ட அடையாளம், முகவரி, புகைப்படம் மற்றும் தொடர்புடைய மருத்துவ/மாற்றுத்திறன் ஆவணங்களைத் தயாரித்து பதிவேற்றவும்.",
            "விண்ணப்பத்தைச் சமர்ப்பித்து, ஒப்புகை அல்லது விண்ணப்ப எண்ணைப் பாதுகாப்பாக வைத்துக்கொள்ளவும்.",
            "விண்ணப்ப நிலையைச் சரிபார்த்து, கேட்டால் மருத்துவ மதிப்பீடு அல்லது ஆவணச் சரிபார்ப்பை முடிக்கவும்.",
            "ஒப்புதல் கிடைத்த பிறகு இணையதளத்தில் உள்ள பதிவிறக்கம்/நிலை விருப்பங்களைப் பயன்படுத்தவும் அல்லது அதிகாரப்பூர்வ உதவி மையத்தைத் தொடர்புகொள்ளவும்."
        ]
        docs = ["இணையதளம் கேட்கும் அடையாளம் மற்றும் முகவரிச் சான்று", "கேட்கப்பட்டால் புகைப்படம் மற்றும் தொடர்பு விவரங்கள்", "கேட்கப்படும் தொடர்புடைய மருத்துவ/மாற்றுத்திறன் ஆவணங்கள்"]
        important = "இந்த வழிகாட்டி UDID/மாற்றுத்திறனாளர் சான்றிதழுக்கானது; எல்லா மாற்றுத்திறனாளர் உதவித் திட்டங்களுக்கும் பொருந்தாது. தற்போதைய விதிகளை அதிகாரப்பூர்வ இணையதளத்தில் சரிபார்க்கவும்."
    elif "UDID / Disability Certificate" in title and language == "mr":
        title = "UDID / दिव्यांगत्व प्रमाणपत्र — अर्ज मार्गदर्शक"
        steps = [
            "अधिकृत UDID पोर्टल उघडा आणि तुम्हाला UDID कार्ड/दिव्यांगत्व प्रमाणपत्रच हवे आहे याची खात्री करा; इतर सहाय्य योजनांची प्रक्रिया वेगळी असू शकते.",
            "पोर्टलवरील सध्याच्या सूचना वाचा आणि नवीन अर्ज/नोंदणीचा पर्याय निवडा.",
            "अर्जदाराची माहिती अचूक भरा आणि सूचनेनुसार जिल्हा/वैद्यकीय प्राधिकरण निवडा.",
            "पोर्टलने मागितलेले ओळखपत्र, पत्त्याचा पुरावा, फोटो आणि संबंधित वैद्यकीय/दिव्यांगत्व कागदपत्रे तयार करून अपलोड करा.",
            "अर्ज सबमिट करून पावती किंवा अर्ज क्रमांक जतन करा.",
            "अर्जाची स्थिती तपासा. मागणी असल्यास वैद्यकीय मूल्यांकन किंवा कागदपत्र पडताळणी पूर्ण करा.",
            "मंजुरीनंतर पोर्टलवरील डाउनलोड/स्थिती पर्याय वापरा किंवा अधिकृत मदत केंद्राशी संपर्क साधा."
        ]
        docs = ["पोर्टलने मागितलेला ओळख व पत्त्याचा पुरावा", "मागितल्यास फोटो आणि संपर्क तपशील", "पोर्टलने मागितलेली संबंधित वैद्यकीय/दिव्यांगत्व कागदपत्रे"]
        important = "हा मार्गदर्शक UDID/दिव्यांगत्व प्रमाणपत्रासाठी आहे; सर्व दिव्यांग सहाय्य योजनांसाठी नाही. सध्याचे नियम अधिकृत पोर्टलवर तपासा."
    # All catalogue guides should follow the selected Hindi UI language, not leak English templates.
    if language == "hi" and "National Scholarship Portal" not in title and "UDID / Disability Certificate" not in title and "Disability Support" not in title and not any(x in title for x in ["DigiLocker — डिजिटल दस्तावेज़ डाउनलोड गाइड", "PM Surya Ghar — रूफटॉप सोलर सब्सिडी गाइड"]):
        scheme_name = title.split(" — ")[0].strip()
        if scheme_name == "DigiLocker":
            title = "DigiLocker — उपयोग करने की चरण-दर-चरण मार्गदर्शिका"
            steps = [
                "आधिकारिक वेबसाइट https://www.digilocker.gov.in/ खोलें और Sign Up या Sign In चुनें।",
                "पोर्टल पर दिए गए मौजूदा निर्देशों के अनुसार मोबाइल/पहचान सत्यापन पूरा करें; OTP किसी के साथ साझा न करें।",
                "खाता बनाकर लॉग इन करें।",
                "सरकारी संस्थाओं से उपलब्ध दस्तावेज़ पाने के लिए Issued Documents देखें; निजी फाइल के लिए उपलब्ध Upload Documents विकल्प इस्तेमाल करें।",
                "दस्तावेज़ जारी करने वाली संस्था और विवरण जांचें; केवल जरूरत होने पर डाउनलोड या साझा करें।"
            ]
            docs = ["आपके उपयोग में रहने वाला मोबाइल नंबर", "साइन-अप प्रक्रिया में मांगी गई पहचान संबंधी जानकारी"]
            important = "उपलब्ध दस्तावेज़ संबंधित जारीकर्ता पर निर्भर करते हैं।"
        elif scheme_name == "Aadhaar Services":
            title = "आधार सेवाएँ — आवेदन/अपडेट मार्गदर्शिका"
            steps = [
                "https://uidai.gov.in/ खोलें और सही सेवा चुनें—नया नामांकन, विवरण अपडेट, दस्तावेज़ अपडेट, PVC कार्ड या स्थिति जांच।",
                "देखें कि चुनी गई सेवा ऑनलाइन उपलब्ध है या Aadhaar Seva Kendra जाना/अपॉइंटमेंट लेना जरूरी है।",
                "उस विशेष बदलाव के लिए UIDAI द्वारा स्वीकार किए गए प्रमाणों की सूची पढ़ें।",
                "ऑनलाइन अनुरोध पूरा करें या अधिकृत केंद्र पर जाकर सत्यापन कराएं।",
                "मिली हुई URN/SRN/रसीद सुरक्षित रखें और आधिकारिक स्थिति सेवा से ट्रैक करें।"
            ]
            docs = ["सेवा के अनुसार आधार विवरण", "UIDAI की उस सेवा के लिए स्वीकार्य दस्तावेज़"]
            important = "दस्तावेज़ और ऑनलाइन उपलब्धता चुनी गई सेवा के अनुसार अलग हो सकती है।"
        elif scheme_name == "Passport Seva":
            title = "Passport Seva — पासपोर्ट आवेदन मार्गदर्शिका"
            steps = [
                "https://www.passportindia.gov.in/ खोलें और पंजीकरण करें या लॉग इन करें।",
                "Fresh Passport, Re-issue या अपनी जरूरत की सही सेवा चुनें और Document Advisor पढ़ें।",
                "आवेदन भरें और पोर्टल के निर्देश के अनुसार शुल्क/अपॉइंटमेंट पूरा करें।",
                "अपॉइंटमेंट पर मांगे गए मूल दस्तावेज़ और प्रतियां लेकर अधिकृत केंद्र जाएं।",
                "जहां जरूरी हो पुलिस सत्यापन पूरा करें और आवेदन संदर्भ संख्या से स्थिति ट्रैक करें।"
            ]
            docs = ["Document Advisor द्वारा आपके मामले के लिए मांगे गए दस्तावेज़", "आवेदन/अपॉइंटमेंट संदर्भ संख्या"]
            important = "सही दस्तावेज़ सूची आपकी स्थिति और चुनी गई सेवा पर निर्भर करती है।"
        elif scheme_name == "Parivahan Sewa":
            title = "Parivahan Sewa — आवेदन मार्गदर्शिका"
            steps = [
                "https://parivahan.gov.in/ खोलें और राज्य व सही सेवा चुनें—Learner Licence, Driving Licence या वाहन सेवा।",
                "उस सेवा और राज्य के पात्रता नियम व दस्तावेज़ पढ़ें।",
                "फॉर्म भरें और मांगे गए प्रमाण अपलोड करें।",
                "जहां लागू हो, आधिकारिक शुल्क भरें और टेस्ट/अपॉइंटमेंट बुक करें।",
                "जरूरी टेस्ट या सत्यापन पूरा करें और पोर्टल पर स्थिति देखें।"
            ]
            docs = ["सेवा के अनुसार आयु/पता प्रमाण", "मौजूदा लाइसेंस या वाहन विवरण, यदि मांगा जाए"]
            important = "प्रक्रिया राज्य और सेवा के अनुसार बदलती है।"
        elif scheme_name == "PM-KISAN":
            title = "PM-KISAN — पंजीकरण मार्गदर्शिका"
            steps = [
                "https://pmkisan.gov.in/ खोलें और वर्तमान पात्रता तथा अपवर्जन नियम पढ़ें।",
                "पोर्टल पर उपलब्ध New Farmer Registration चुनें या वर्तमान प्रक्रिया के लिए अधिकृत CSC/कृषि कार्यालय से सहायता लें।",
                "किसान, भूमि और बैंक विवरण आधिकारिक रिकॉर्ड के अनुसार भरें।",
                "निर्देशानुसार e-KYC और भूमि रिकॉर्ड सत्यापन पूरा करें।",
                "पंजीकरण विवरण सुरक्षित रखें और आधिकारिक पोर्टल पर लाभार्थी/स्थिति जांचें।"
            ]
            docs = ["भूमि रिकॉर्ड/खातेदारी विवरण", "पंजीकरण प्रक्रिया में मांगे गए पहचान और बैंक विवरण"]
            important = "पात्रता, भूमि सत्यापन और अपवर्जन नियम आधिकारिक पोर्टल पर जांचें।"
        elif scheme_name == "PM Fasal Bima Yojana":
            title = "प्रधानमंत्री फसल बीमा योजना — आवेदन मार्गदर्शिका"
            steps = [
                "https://pmfby.gov.in/ खोलें और जांचें कि आपके राज्य, जिले, फसल और मौसम के लिए योजना अधिसूचित है या नहीं।",
                "वर्तमान मौसम की नामांकन समय-सीमा, प्रीमियम और पात्रता नियम पढ़ें; पुरानी तारीखों पर भरोसा न करें।",
                "अपने मामले के लिए पोर्टल द्वारा बताए गए अधिकृत बैंक/CSC/अन्य चैनल से आवेदन करें।",
                "फसल, भूमि/किरायेदारी और बैंक विवरण सही भरें तथा मांगे गए दस्तावेज़ जमा करें।",
                "रसीद सुरक्षित रखें और नुकसान/दावे की स्थिति में आधिकारिक रिपोर्टिंग समय-सीमा का पालन करें।"
            ]
            docs = ["फसल, मौसम और भूमि/किरायेदारी विवरण, जैसा मांगा जाए", "अधिकृत चैनल द्वारा मांगे गए बैंक और पहचान विवरण"]
            important = "फसल और मौसम के अनुसार नियम तथा तारीखें बदलती हैं; वर्तमान अधिसूचना जांचें।"
        else:
            steps = [
                f"आधिकारिक पोर्टल {guide['official_url']} खोलें और “{scheme_name}” से संबंधित वर्तमान अनुभाग/सूचना खोजें।",
                "योजना के आधिकारिक दिशा-निर्देश पढ़ें: कौन आवेदन कर सकता है, राज्य/आयु/आय/कोर्स/व्यवसाय की क्या शर्तें हैं और आवेदन अभी स्वीकार हो रहे हैं या नहीं।",
                "यदि योजना आपके लिए लागू हो, तो पोर्टल पर बताए गए ऑनलाइन, बैंक, स्थानीय कार्यालय या अधिकृत सेवा-केंद्र के सही रास्ते का उपयोग करें; हर योजना का आवेदन तरीका एक जैसा नहीं होता।",
                "केवल वर्तमान निर्देशों में मांगे गए दस्तावेज़ तैयार करें। नीचे दी गई सूची तैयारी के लिए है, अनिवार्य या पूरी आधिकारिक सूची नहीं।",
                "विवरण सही भरें, मांगे गए प्रमाण जमा करें और सबमिट करने से पहले फॉर्म जांचें। जहां व्यक्तिगत सत्यापन/बैंक/स्थानीय कार्यालय की प्रक्रिया बताई गई हो, उसे पूरा करें।",
                "रसीद/आवेदन/संदर्भ संख्या सुरक्षित रखें और आधिकारिक पोर्टल या विभाग द्वारा बताए गए माध्यम से स्थिति ट्रैक करें।",
                "यदि विभाग सुधार या अतिरिक्त सत्यापन मांगे, तो आधिकारिक निर्देशों और बताई गई समय-सीमा के अनुसार जवाब दें।"
            ]
            docs_map = {
                "Education": ["कोर्स/संस्थान विवरण", "अंकपत्र या शैक्षणिक प्रमाण, यदि मांगा जाए", "आय/श्रेणी प्रमाणपत्र केवल यदि योजना मांगे", "बैंक/पहचान दस्तावेज़ केवल आधिकारिक सूची के अनुसार"],
                "Documents": ["सेवा के लिए आवश्यक पहचान/संपर्क विवरण", "उस विशेष सेवा के लिए आधिकारिक तौर पर स्वीकार प्रमाण", "स्थिति ट्रैक करने के लिए रसीद/संदर्भ संख्या"],
                "Healthcare": ["लाभार्थी/परिवार और पहचान विवरण, जैसा मांगा जाए", "लागू होने पर मौजूदा स्वास्थ्य कार्ड/रिकॉर्ड", "चिकित्सा/मातृत्व रिकॉर्ड केवल यदि योजना मांगे"],
                "Farmers": ["किसान, भूमि या फसल विवरण, जैसा सेवा मांगे", "आधिकारिक प्रक्रिया के अनुसार बैंक/पहचान विवरण", "बीमा/ऋण के लिए संबंधित फसल या भूमि प्रमाण, यदि मांगा जाए"],
                "Housing": ["परिवार और निवास विवरण", "आय/घर/आवास संबंधी प्रमाण, यदि योजना मांगे", "पहचान/बैंक विवरण केवल आधिकारिक नियमों के अनुसार"],
                "Jobs": ["पहचान और संपर्क विवरण", "शैक्षणिक/कौशल प्रमाणपत्र, यदि लागू हो", "बैंक विवरण केवल संबंधित लाभ के लिए आवश्यक होने पर"],
                "Women": ["लाभार्थी/अभिभावक और परिवार विवरण, जैसा लागू हो", "जन्म/गर्भावस्था/पोषण संबंधी रिकॉर्ड केवल यदि कार्यक्रम मांगे"],
                "Finance": ["पहचान और संपर्क विवरण", "बैंक विवरण, जैसा बैंक/योजना मांगे", "आयु/नामांकित व्यक्ति/सहमति विवरण, यदि जरूरी हो"],
                "Business": ["व्यवसाय/गतिविधि विवरण", "पोर्टल या ऋणदाता द्वारा मांगे गए पहचान/पता/बैंक रिकॉर्ड", "व्यवसाय योजना/पंजीकरण प्रमाण केवल यदि मांगा जाए"],
                "Digital": ["सेवा के अनुसार परिवार/पता/लाभार्थी विवरण", "पहचान/संपर्क जानकारी, यदि आवश्यक हो", "पोर्टल द्वारा बताई गई सेवा-विशिष्ट जानकारी"]
            }
            docs = docs_map.get(guide.get("category", ""), ["आधिकारिक पोर्टल पर मांगे गए पहचान और सेवा-संबंधी दस्तावेज़"])
            important = "यह सामान्य मार्गदर्शन है, लाइव पात्रता/आवेदन खुला होने/लाभ स्वीकृति की पुष्टि नहीं। वर्तमान नियम, दस्तावेज़, शुल्क और समय-सीमा आधिकारिक पोर्टल पर जांचें।"
    # Scheme-specific translations: BBBP is a programme, not a universal cash application.
    if "Beti Bachao Beti Padhao" in title and language == "bn":
        title = "বেটি বাঁচাও বেটি পড়াও — কর্মসূচির নির্দেশিকা"
        steps = [
            "নারী ও শিশু উন্নয়ন মন্ত্রকের সরকারি ওয়েবসাইট https://wcd.gov.in/ খুলুন এবং Beti Bachao Beti Padhao-এর বর্তমান নির্দেশিকা ও বিজ্ঞপ্তি খুঁজুন।",
            "মনে রাখুন, BBBP মূলত কন্যাশিশুর মর্যাদা, সুরক্ষা ও শিক্ষার প্রসারের কর্মসূচি; এটি প্রত্যেক পরিবারের জন্য সর্বজনীন সরাসরি নগদ-সহায়তার আবেদন প্রকল্প নয়।",
            "স্থানীয় সচেতনতা বা সামাজিক কার্যক্রমে অংশ নিতে চাইলে জেলা নারী ও শিশু উন্নয়ন দপ্তর, District Programme Officer বা জেলা প্রশাসনের সঙ্গে যোগাযোগ করে বর্তমান কার্যক্রম সম্পর্কে জিজ্ঞাসা করুন।",
            "কন্যাশিশুর জন্য আর্থিক সহায়তা বা বৃত্তি চাইলে সংশ্লিষ্ট আলাদা কেন্দ্রীয়/রাজ্য প্রকল্পের নাম শনাক্ত করুন এবং তার নিজস্ব যোগ্যতা ও আবেদন-পদ্ধতি যাচাই করুন।",
            "যে কোনও আবেদন শুধু সংশ্লিষ্ট সরকারি দপ্তর বা রাজ্য পোর্টালের মাধ্যমে করুন। দালালকে টাকা দেবেন না এবং OTP, পাসওয়ার্ড বা ব্যাংক PIN শেয়ার করবেন না।",
            "বর্তমান কার্যক্রম, যোগ্যতা এবং উপলব্ধ সুবিধা সরকারি দপ্তরে যাচাই করুন; এই নির্দেশিকা আবেদন বর্তমানে খোলা আছে বলে নিশ্চয়তা দেয় না।"
        ]
        docs = [
            "সাধারণ BBBP কার্যক্রমে অংশগ্রহণের জন্য সবার ক্ষেত্রে প্রযোজ্য একক নথির তালিকা নেই; জেলা দপ্তরে জেনে নিন।",
            "আলাদা বৃত্তি বা সুবিধার জন্য সেই প্রকল্পে চাওয়া পরিচয়, বাসস্থান, বয়স, আয় বা শিক্ষার নথি প্রস্তুত করুন।"
        ]
        important = "BBBP সাধারণত প্রত্যেক মেয়ে বা পরিবারকে সরাসরি নগদ অর্থ দেওয়ার প্রকল্প নয়। অর্থ বা আবেদনের কোনও দাবি সরকারি নারী ও শিশু উন্নয়ন দপ্তরে যাচাই করুন।"
    elif "Beti Bachao Beti Padhao" in title and language == "hi":
        title = "बेटी बचाओ बेटी पढ़ाओ — योजना मार्गदर्शिका"
        steps = [
            "महिला एवं बाल विकास मंत्रालय की आधिकारिक वेबसाइट https://wcd.gov.in/ खोलें और BBBP की वर्तमान गाइडलाइन व सूचनाएँ देखें।",
            "ध्यान दें कि BBBP मुख्यतः बालिकाओं के संरक्षण, सम्मान और शिक्षा को बढ़ावा देने वाला कार्यक्रम है; यह हर परिवार के लिए सीधे नकद राशि पाने की सार्वभौमिक आवेदन योजना नहीं है।",
            "स्थानीय जागरूकता या सामुदायिक गतिविधियों में भाग लेने के लिए जिला महिला एवं बाल विकास कार्यालय, District Programme Officer या जिला प्रशासन से वर्तमान गतिविधियों की जानकारी लें।",
            "यदि बालिका के लिए आर्थिक सहायता या छात्रवृत्ति चाहिए, तो संबंधित अलग केंद्र/राज्य योजना पहचानें और उसकी पात्रता तथा आवेदन प्रक्रिया जाँचें।",
            "किसी भी आवेदन के लिए संबंधित आधिकारिक विभाग या राज्य पोर्टल का ही उपयोग करें। एजेंट को पैसे न दें और OTP, पासवर्ड या बैंक PIN साझा न करें।",
            "वर्तमान गतिविधियों, पात्रता और उपलब्ध लाभों की पुष्टि सरकारी विभाग से करें; यह गाइड आवेदन खुला होने की पुष्टि नहीं करती।"
        ]
        docs = ["BBBP गतिविधियों में सामान्य भागीदारी के लिए एक सार्वभौमिक दस्तावेज़ सूची नहीं है; जिला कार्यालय से पूछें।", "अलग छात्रवृत्ति/लाभ के लिए उसी योजना में माँगे गए पहचान, निवास, आयु, आय या शिक्षा संबंधी दस्तावेज़ तैयार करें।"]
        important = "BBBP सामान्यतः हर बालिका या परिवार को सीधे नकद राशि देने वाली योजना नहीं है। पैसे या आवेदन से जुड़े दावों को आधिकारिक विभाग से सत्यापित करें।"
    elif "Beti Bachao Beti Padhao" in title and language == "en":
        title = "Beti Bachao Beti Padhao — Programme Guide"
        steps = [
            "Open the Ministry of Women and Child Development website at https://wcd.gov.in/ and look for the current BBBP guidelines and notices.",
            "BBBP primarily promotes the protection, dignity and education of the girl child; it is not a universal direct-cash application scheme for every family.",
            "To join local awareness or community activities, contact the district Women and Child Development office, District Programme Officer or district administration and ask about current activities.",
            "If you need financial assistance or a scholarship for a girl child, identify the separate central/state scheme and check its own eligibility and application process.",
            "Use only the relevant official department or state portal. Do not pay agents or share OTPs, passwords or bank PINs.",
            "Confirm current activities, eligibility and available benefits with the official department; this guide does not confirm that applications are open."
        ]
        docs = ["There is no universal individual document list for general BBBP participation; ask the district office about the activity.", "For a separate scholarship or benefit, prepare only the identity, residence, age, income or education documents required by that scheme."]
        important = "BBBP is not generally a direct-cash benefit paid automatically to every girl or family. Verify claims about money or applications with the official department."
    # Generic guide translations ensure that non-NSP catalogue answers also respect
    # Bengali, Tamil and Telugu UI selection instead of leaking English steps.
    special_titles = [
        "DigiLocker — ডিজিটাল নথি ডাউনলোড নির্দেশিকা",
        "DigiLocker — Download Your Documents",
        "PM Surya Ghar — ছাদের সৌরবিদ্যুৎ ভর্তুকি নির্দেশিকা",
        "PM Surya Ghar — Rooftop Solar Subsidy Guide",
        "ন্যাশনাল স্কলারশিপ পোর্টাল (NSP)",
        "Beti Bachao Beti Padhao",
        "UDID / Disability Certificate"
    ]
    if language in ("bn", "ta", "te") and not any(x in title for x in special_titles):
        scheme_name = title.split(" — ")[0].strip()
        if language == "bn":
            title = f"{scheme_name} — আবেদন নির্দেশিকা"
            steps = [
                f"সরকারি পোর্টালটি খুলুন: {guide['official_url']}।",
                f"{scheme_name}-এর বিভাগে গিয়ে বর্তমান সরকারি নির্দেশিকা, যোগ্যতার শর্ত এবং আবেদন এখন গ্রহণ করা হচ্ছে কি না তা যাচাই করুন।",
                "আপনার ক্ষেত্রে প্রযোজ্য রাজ্য, বয়স, আয়, কোর্স, পেশা, পরিবার বা উপভোক্তা-সংক্রান্ত শর্তগুলি মিলিয়ে নিন।",
                "পোর্টালের নির্দেশ অনুযায়ী সঠিক আবেদনপথ বেছে নিন। কিছু পরিষেবায় অনলাইন ফর্ম লাগে, অন্য ক্ষেত্রে ব্যাঙ্ক, স্থানীয় দপ্তর বা অনুমোদিত পরিষেবা কেন্দ্রে যেতে হতে পারে।",
                "বর্তমান নির্দেশিকায় স্পষ্টভাবে চাওয়া নথিগুলিই প্রস্তুত করুন; নিচের তালিকা কেবল প্রস্তুতির সহায়ক, বাধ্যতামূলক সরকারি তালিকা নয়।",
                "সঠিক তথ্য পূরণ করুন, চাওয়া নথি আপলোড করুন, ফর্ম যাচাই করে জমা দিন অথবা নির্দেশিত সরাসরি যাচাই সম্পন্ন করুন।",
                "রসিদ বা আবেদন/রেফারেন্স নম্বর পেলে সংরক্ষণ করুন।",
                "সরকারি পোর্টাল বা দপ্তরের যোগাযোগপথে আবেদন-স্থিতি দেখুন এবং অতিরিক্ত যাচাই বা সংশোধনের অনুরোধ পূরণ করুন।"
            ]
            docs = ["পরিষেবা অনুযায়ী পরিচয় ও যোগাযোগের তথ্য", "শুধু পোর্টাল চাইলে আয়/শ্রেণি/বাসস্থান/শিক্ষা/ব্যাঙ্কের নথি", "আবেদন নম্বর বা রসিদ, যদি দেওয়া হয়"]
            important = "এটি সাধারণ নির্দেশিকা; যোগ্যতা, আবেদন খোলা থাকা, অনুমোদন বা সময়সীমার নিশ্চয়তা নয়। বর্তমান নিয়ম সরকারি পোর্টালে যাচাই করুন।"
        elif language == "ta":
            title = f"{scheme_name} — விண்ணப்ப வழிகாட்டி"
            steps = [
                f"அதிகாரப்பூர்வ இணையதளத்தைத் திறக்கவும்: {guide['official_url']}",
                f"{scheme_name} பகுதியைத் திறந்து தற்போதைய அதிகாரப்பூர்வ விதிகள், தகுதி நிபந்தனைகள் மற்றும் விண்ணப்பங்கள் ஏற்கப்படுகிறதா என்பதைச் சரிபார்க்கவும்.",
                "உங்கள் மாநிலம், வயது, வருமானம், படிப்பு, தொழில், குடும்பம் அல்லது பயனாளி வகைக்கு பொருந்தும் நிபந்தனைகளைச் சரிபார்க்கவும்.",
                "இணையதளத்தின் தற்போதைய வழிமுறைகளின்படி சரியான விண்ணப்ப முறையைத் தேர்ந்தெடுக்கவும். சில சேவைகளுக்கு வங்கி, உள்ளூர் அலுவலகம் அல்லது அங்கீகரிக்கப்பட்ட சேவை மையம் தேவைப்படலாம்.",
                "தற்போதைய விதிகளில் குறிப்பாகக் கேட்கப்படும் ஆவணங்களை மட்டும் தயார் செய்யவும்; கீழே உள்ள பட்டியல் தயாரிப்புக்கான உதவி மட்டுமே.",
                "சரியான விவரங்களை நிரப்பி, கேட்கப்பட்ட ஆவணங்களைப் பதிவேற்றி, படிவத்தைச் சரிபார்த்து சமர்ப்பிக்கவும் அல்லது கூறப்பட்ட நேரடி சரிபார்ப்பை முடிக்கவும்.",
                "ரசீது அல்லது விண்ணப்ப/குறிப்பு எண்ணை வழங்கினால் பாதுகாப்பாக வைத்துக்கொள்ளவும்.",
                "அதிகாரப்பூர்வ இணையதளம் அல்லது துறை தொடர்பு வழியாக நிலையைப் பார்க்கவும்; கூடுதல் சரிபார்ப்பு அல்லது திருத்தக் கோரிக்கைகளை நிறைவேற்றவும்."
            ]
            docs = ["சேவைக்குத் தேவையான அடையாளம் மற்றும் தொடர்பு விவரங்கள்", "இணையதளம் கேட்டால் மட்டுமே வருமானம்/வகுப்பு/முகவரி/கல்வி/வங்கி ஆவணங்கள்", "வழங்கப்பட்டால் விண்ணப்ப எண் அல்லது ரசீது"]
            important = "இது பொதுவான வழிகாட்டுதல் மட்டுமே; தகுதி, விண்ணப்பம் திறந்திருப்பது, ஒப்புதல் அல்லது காலக்கெடுவை உறுதி செய்யாது. தற்போதைய விதிகளை அதிகாரப்பூர்வ தளத்தில் சரிபார்க்கவும்."
        else:
            title = f"{scheme_name} — దరఖాస్తు మార్గదర్శిని"
            steps = [
                f"అధికారిక పోర్టల్‌ను తెరవండి: {guide['official_url']}.",
                f"{scheme_name} విభాగంలో ప్రస్తుత అధికారిక మార్గదర్శకాలు, అర్హత షరతులు మరియు దరఖాస్తులు ప్రస్తుతం స్వీకరిస్తున్నారా అనేది తనిఖీ చేయండి.",
                "మీ రాష్ట్రం, వయస్సు, ఆదాయం, కోర్సు, వృత్తి, కుటుంబం లేదా లబ్ధిదారుల వర్గానికి వర్తించే షరతులను సరిపోల్చండి.",
                "పోర్టల్ సూచనల ప్రకారం సరైన దరఖాస్తు మార్గాన్ని ఎంచుకోండి. కొన్ని సేవలకు బ్యాంకు, స్థానిక కార్యాలయం లేదా అధీకృత సేవా కేంద్రాన్ని సందర్శించాల్సి రావచ్చు.",
                "ప్రస్తుత మార్గదర్శకాల్లో స్పష్టంగా కోరిన పత్రాలనే సిద్ధం చేయండి; దిగువ జాబితా సిద్ధత కోసం మాత్రమే, తప్పనిసరి అధికారిక జాబితా కాదు.",
                "సరైన వివరాలు నమోదు చేసి, కోరిన పత్రాలను అప్‌లోడ్ చేసి, ఫారమ్‌ను సమీక్షించి సమర్పించండి లేదా సూచించిన ప్రత్యక్ష ధృవీకరణను పూర్తి చేయండి.",
                "రసీదు లేదా దరఖాస్తు/రిఫరెన్స్ నంబర్ ఇస్తే భద్రపరచండి.",
                "అధికారిక పోర్టల్ లేదా శాఖ సంప్రదింపు మార్గం ద్వారా స్థితిని పరిశీలించి, కోరిన ధృవీకరణ లేదా సవరణలను పూర్తి చేయండి."
            ]
            docs = ["సేవకు సంబంధించిన గుర్తింపు మరియు సంప్రదింపు వివరాలు", "పోర్టల్ అడిగితే మాత్రమే ఆదాయం/వర్గం/చిరునామా/విద్య/బ్యాంకు పత్రాలు", "ఇస్తే దరఖాస్తు సంఖ్య లేదా రసీదు"]
            important = "ఇది సాధారణ మార్గదర్శకం మాత్రమే; అర్హత, దరఖాస్తులు తెరిచి ఉండటం, ఆమోదం లేదా గడువును నిర్ధారించదు. ప్రస్తుత నియమాలను అధికారిక పోర్టల్‌లో తనిఖీ చేయండి."

    # English UI must never receive Hindi-only deterministic fallback text.
    if language == "en" and not any(x in title for x in ["DigiLocker — Download Your Documents", "PM Surya Ghar — Rooftop Solar Subsidy Guide"]):
        if "National Scholarship Portal" in title:
            title = "National Scholarship Portal (NSP) — Application Guide"
            steps = [
                "Open the official NSP portal https://scholarships.gov.in/ and check notices for the current academic year.",
                "Read the selected scholarship guidelines and check course, institution, state, category, family-income and other eligibility rules.",
                "Complete One Time Registration (OTR) if the portal currently requires it, following the portal's instructions.",
                "Sign in and select only a scholarship whose published conditions you meet.",
                "Enter personal, academic, institution and bank details accurately; do not guess missing information.",
                "Upload only the documents requested by the selected scheme, in the specified format and size.",
                "Review the application, submit it and save the acknowledgement/application number.",
                "Track the status on the portal and complete any institution/department verification or correction requested."
            ]
            docs = ["Course, year and institution details", "Income/category/disability certificate only if the selected scheme requires it", "Bank details as specified by the portal", "Identity/contact documents listed in the current scheme guidelines"]
            important = "This is general navigation guidance, not confirmation of eligibility or an open application window. Verify current requirements and deadlines on the official portal. Never share OTPs, passwords or bank PINs."
        elif "Disability Support" in title or "UDID / Disability Certificate" in title:
            title = "Disability Support — choose the service you need"
            steps = [
                "First identify the service you need: a UDID/disability certificate, pension, scholarship, assistive device, travel concession or another benefit. Each may have a different process.",
                "For a UDID card/disability certificate, open https://swavlambancard.gov.in/ and read the current official instructions.",
                "Choose the new application/registration option shown on the portal, enter the applicant details, and select the district/medical authority as instructed.",
                "Prepare and upload only the identity, address, photo and medical/disability records requested by the portal.",
                "Submit the application, save the acknowledgement/application number, and track the status on the portal.",
                "Complete any medical assessment or document verification requested. For a different disability benefit, use that benefit's official central/state portal."
            ]
            docs = ["Identity/address proof, photo and relevant medical records only as requested by the UDID portal", "For other benefits, the document list published by that specific scheme"]
            important = "This guide does not confirm eligibility or cover every disability benefit. Verify the current process on the relevant official portal."
        else:
            title = re.sub(r"\s*—\s*आवेदन मार्गदर्शिका|\s*—\s*आवेदन गाइड|\s*—\s*अर्ज मार्गदर्शक", " — Application Guide", title)
            steps = [
                f"Open the official portal for this service: {guide['official_url']}.",
                f"Find the section for {title.split(' — ')[0]} and read the latest official instructions, eligibility conditions and whether applications are currently being accepted.",
                "Check the conditions that apply to you, such as state, age, income, course, occupation, household or beneficiary category.",
                "Follow the official instructions for the correct application route. Some services use an online form; others require a bank, local office, authorised service centre or in-person verification.",
                "Prepare only the documents listed in the current instructions. The checklist below is a preparation aid, not a guaranteed mandatory list.",
                "Enter accurate details, upload only requested proofs, review the form and submit it or complete the instructed in-person/bank verification.",
                "Save the acknowledgement/reference number or receipt, if issued.",
                "Track the request using the official portal or department contact channel and complete any requested correction or verification."
            ]
            important = "This is general navigation guidance, not live confirmation of eligibility, application availability, approval or deadlines. Verify current rules, documents, fees and dates on the official portal."
    lines = [title, "", portal_label + " " + guide["official_url"], "", steps_label]
    lines.extend(f"{i}. {step}" for i, step in enumerate(steps, 1))
    lines.extend(["", docs_label])
    lines.extend(f"• {item}" for item in docs)
    lines.extend(["", important_label + " " + important])
    return "\n".join(lines)




def ask_gemini(question, language="en", history=None):
    """Gemini REST API; API key never leaves the Flask server."""
    import json
    import urllib.request
    import urllib.error

    api_key = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6ImMXC8sn7sN33OHZYr45KL3_nL4gg76HcKLinFfM9jfw").strip()
    if not api_key:
        return None, "Gemini API key is not configured. Set GEMINI_API_KEY on the server."

    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    # Model name is server-controlled, never provided by website visitors.
    if not model or not all(c.isalnum() or c in "-_." for c in model):
        return None, "Invalid GEMINI_MODEL configuration."

    catalogue = janseva_search_schemes(question)
    guide = scheme_application_guide(question)
    context = {"local_catalogue_results": catalogue.get("results", [])[:8], "application_guide": guide}
    language_names = {"en":"English", "hi":"Hindi", "bn":"Bengali", "ta":"Tamil", "te":"Telugu", "mr":"Marathi"}
    instructions = (
        f"You are JanSeva AI, a helpful assistant. Respond in {language_names.get(language, 'English')}. "
        "RULE 1 (Government Schemes): If the user asks about Indian government schemes, scholarships, documents, healthcare, farming, jobs, or housing, use the provided catalogue context and application guide accurately. "
        "RULE 2 (General Knowledge - STRICT): If the user asks ANY general knowledge question (such as 'Who is the Prime Minister of India?', current affairs, science, math, or coding), YOU MUST ANSWER DIRECTLY AND FACTUALLY using your internal training data. State the actual name or fact immediately. DO NOT tell the user to check official portals or websites for general knowledge. DO NOT mention your local catalogue for general queries. "
        "Never request passwords, OTPs, PINs or other secret details."
    )
    contents = []
    if isinstance(history, list):
        for turn in history[-10:]:
            if not isinstance(turn, dict):
                continue
            role = turn.get("role")
            text = turn.get("text")
            if role in ("user", "model") and isinstance(text, str) and 0 < len(text) <= 2000:
                contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": question + "\n\nRelevant local catalogue context (not live verified):\n" + json.dumps(context, ensure_ascii=False)}]})
    payload = {"systemInstruction": {"parts": [{"text": instructions}]}, "contents": contents,
               "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1200}}
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": api_key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            result = json.loads(response.read().decode("utf-8"))
        parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        answer = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        return (answer, None) if answer else (None, "Gemini returned no text. Try rephrasing your question.")
    except urllib.error.HTTPError as exc:
        app.logger.warning("Gemini API HTTP %s", exc.code)
        messages = {400: "Gemini rejected the request. Check the model configuration.",
                    401: "Gemini API authentication failed. Check your API key.",
                    403: "Gemini API access denied. Check API key permissions.",
                    404: "Gemini model not found. Check GEMINI_MODEL.",
                    429: "Gemini rate limit or quota reached. Please try later."}
        return None, messages.get(exc.code, "Gemini service is temporarily unavailable (HTTP %s)." % exc.code)
    except (urllib.error.URLError, TimeoutError):
        app.logger.warning("Gemini network request failed")
        return None, "Could not reach Gemini. Please try again."
    except (ValueError, KeyError, IndexError, TypeError):
        app.logger.warning("Gemini response could not be parsed")
        return None, "Gemini returned an unexpected response."


@app.route("/api/assistant", methods=["POST"])
@api_login_required
def assistant():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request."}), 400
    question = data.get("message", "")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Please enter a question."}), 400
    question = question.strip()
    if len(question) > 1500:
        return jsonify({"error": "Question must be 1500 characters or fewer."}), 400
    language = str(data.get("language", "en")).lower()[:8]
    answer, error = ask_gemini(question, language, data.get("history"))
    if error:
        return jsonify({"error": error, "mode": "gemini"}), 503
    return jsonify({"answer": answer, "mode": "gemini"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "AI JanSeva"})

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

# Initialize tables for both `python app.py` and production WSGI servers (e.g. Gunicorn).
init_db()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
