from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, re, random, json
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "freelancehub-dev-secret-change-in-production")
DATABASE = os.path.join(os.path.dirname(__file__), "freelancehub.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

CATEGORY_DEFAULT_IMAGES = {
    "design":      "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=800&h=500&fit=crop",
    "development": "https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&h=500&fit=crop",
    "writing":     "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800&h=500&fit=crop",
    "marketing":   "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&h=500&fit=crop",
    "video":       "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=800&h=500&fit=crop",
    "music":       "https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=800&h=500&fit=crop",
    "data":        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=500&fit=crop",
    "business":    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=500&fit=crop",
}

SERVICE_KEYWORD_IMAGES = {
    "logo":        "https://images.unsplash.com/photo-1558655146-364adaf1fcc9?w=800&h=500&fit=crop",
    "brand":       "https://images.unsplash.com/photo-1634084462412-b54873c0a56d?w=800&h=500&fit=crop",
    "website":     "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=800&h=500&fit=crop",
    "wordpress":   "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=500&fit=crop",
    "seo":         "https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=800&h=500&fit=crop",
    "blog":        "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=800&h=500&fit=crop",
    "social":      "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&h=500&fit=crop",
    "video":       "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=800&h=500&fit=crop",
    "voice":       "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=800&h=500&fit=crop",
    "data":        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=500&fit=crop",
    "excel":       "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800&h=500&fit=crop",
    "business":    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=500&fit=crop",
    "ui":          "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800&h=500&fit=crop",
    "app":         "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=500&fit=crop",
}

def get_service_image(title, description, category_slug):
    text = (title + " " + description).lower()
    for keyword, url in SERVICE_KEYWORD_IMAGES.items():
        if keyword in text:
            return url
    return CATEGORY_DEFAULT_IMAGES.get(category_slug, "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=500&fit=crop")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'buyer',
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                avatar_url TEXT,
                bio TEXT,
                location TEXT,
                website TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                icon TEXT NOT NULL,
                description TEXT
            );
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                delivery_days INTEGER DEFAULT 3,
                category_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                tags TEXT DEFAULT '[]',
                image_url TEXT,
                view_count INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
                FOREIGN KEY (reviewer_id) REFERENCES users(id),
                UNIQUE(service_id, reviewer_id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                payment_method TEXT,
                payment_ref TEXT,
                total_price INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (buyer_id) REFERENCES users(id),
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (buyer_id) REFERENCES users(id),
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                inquiry_id INTEGER,
                sender_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (sender_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                link TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                message TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                admin_reply TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS saved_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, service_id)
            );
        """)
        seed_data(db)

def seed_data(db):
    count = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if count > 0:
        return
    categories = [
        ("Design", "design", "🎨", "Logos, branding, UI/UX and more"),
        ("Development", "development", "💻", "Web, mobile and software development"),
        ("Writing", "writing", "✍️", "Content, copywriting, and translation"),
        ("Marketing", "marketing", "📣", "SEO, social media, and ads"),
        ("Video", "video", "🎬", "Editing, animation, and production"),
        ("Music & Audio", "music", "🎵", "Voice over, music, and audio"),
        ("Data & Analytics", "data", "📊", "Data analysis, Excel, and BI"),
        ("Business", "business", "💼", "Business plans, consulting, and finance"),
    ]
    db.executemany("INSERT INTO categories (name, slug, icon, description) VALUES (?, ?, ?, ?)", categories)
    admin = [("Admin User", "admin@freelancehub.com", generate_password_hash("admin123"), "seller", 1)]
    sellers = [
        ("Alice Chen", "alice@demo.com", generate_password_hash("password123"), "seller", 0),
        ("Bob Patel", "bob@demo.com", generate_password_hash("password123"), "seller", 0),
        ("David Kim", "david@demo.com", generate_password_hash("password123"), "seller", 0),
    ]
    buyer = [("Carol Smith", "carol@demo.com", generate_password_hash("password123"), "buyer", 0)]
    for u in admin + sellers + buyer:
        db.execute("INSERT OR IGNORE INTO users (name, email, password_hash, role, is_admin) VALUES (?, ?, ?, ?, ?)", u)
    cat = {row["slug"]: row["id"] for row in db.execute("SELECT id, slug FROM categories")}
    user = {row["email"]: row["id"] for row in db.execute("SELECT id, email FROM users")}
    alice, bob, david = user["alice@demo.com"], user["bob@demo.com"], user["david@demo.com"]
    services = [
        ("Professional Logo Design", "Eye-catching logos that represent your brand perfectly. Includes unlimited revisions until you are 100% satisfied. Source files (AI, EPS, PNG, SVG) included. I create logos that are unique, memorable, and perfectly tailored to your business identity.", 5999, 3, cat["design"], alice, '["logo","branding","vector"]', "https://images.unsplash.com/photo-1558655146-364adaf1fcc9?w=800&h=500&fit=crop", 245),
        ("Modern Website Development", "Full-stack responsive website with React or plain HTML/CSS. Includes hosting setup, contact form, and SEO basics. I build fast, mobile-first websites that convert visitors into customers.", 29999, 7, cat["development"], bob, '["web","react","responsive"]', "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=800&h=500&fit=crop", 312),
        ("SEO Blog Content Writing", "Professionally written, keyword-optimised blog posts that rank on Google. 1000-2000 words per article. Research-backed, engaging, and designed to drive organic traffic.", 3499, 2, cat["writing"], david, '["seo","blog","content"]', "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=800&h=500&fit=crop", 178),
        ("Social Media Marketing Strategy", "Complete 30-day strategy with content calendar, hashtag research, and analytics reporting. I help brands grow their Instagram, Facebook, and LinkedIn presence.", 16999, 5, cat["marketing"], alice, '["social","instagram","strategy"]', "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&h=500&fit=crop", 428),
        ("Professional Video Editing", "Hollywood-style video editing with colour grading, transitions, and background music. Up to 5 minutes. Your raw footage transformed into a cinematic masterpiece.", 9999, 4, cat["video"], bob, '["video","editing","youtube"]', "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=800&h=500&fit=crop", 203),
        ("Voice Over Recording", "Studio-quality voice over in English. Clear, professional delivery. Up to 500 words. Perfect for explainer videos, ads, e-learning modules, and podcasts.", 4999, 1, cat["music"], david, '["voiceover","audio","narration"]', "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=800&h=500&fit=crop", 156),
        ("Brand Identity Package", "Complete brand kit: logo, colour palette, typography, business card, and brand guidelines. Everything you need to present a unified, professional brand.", 37999, 10, cat["design"], alice, '["branding","identity","design"]', "https://images.unsplash.com/photo-1634084462412-b54873c0a56d?w=800&h=500&fit=crop", 534),
        ("WordPress Website Development", "Custom WordPress site with a premium theme, plugins, SEO setup, and 1 month of support. Fast, secure, and easy for you to manage.", 23999, 6, cat["development"], bob, '["wordpress","cms","website"]', "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=500&fit=crop", 267),
        ("Data Analysis & Excel Dashboard", "Automated Excel/Google Sheets dashboards with charts, pivot tables, and KPI tracking. Transform your raw data into actionable insights.", 7999, 3, cat["data"], david, '["excel","data","dashboard"]', "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=500&fit=crop", 142),
        ("Business Plan Writing", "Investor-ready business plans with financial projections, market analysis, and executive summary. Help startups and SMEs present their vision compellingly.", 14999, 7, cat["business"], alice, '["business","plan","startup"]', "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=500&fit=crop", 334),
    ]
    db.executemany(
        "INSERT INTO services (title, description, price, delivery_days, category_id, seller_id, tags, image_url, view_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        services
    )
    carol = user["carol@demo.com"]
    svc_ids = [row["id"] for row in db.execute("SELECT id FROM services ORDER BY id LIMIT 6")]
    reviews_seed = [
        (svc_ids[0], carol, 5, "Absolutely stunning work! Alice delivered beyond expectations."),
        (svc_ids[1], carol, 4, "Great website, very professional. Our conversions improved significantly."),
        (svc_ids[2], carol, 5, "David is a brilliant writer. The blog posts ranked within a week!"),
        (svc_ids[3], carol, 4, "Solid strategy. Saw real growth on Instagram within 2 weeks."),
        (svc_ids[4], carol, 5, "My YouTube channel looks professional now. Highly recommended!"),
        (svc_ids[5], carol, 4, "Clear, professional voice over. Delivered on time."),
    ]
    for rv in reviews_seed:
        db.execute("INSERT OR IGNORE INTO reviews (service_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)", rv)
    db.execute("""
        INSERT INTO orders (service_id, buyer_id, seller_id, status, payment_method, total_price, notes)
        VALUES (?, ?, ?, 'completed', 'upi', ?, 'Please use dark navy blue as primary colour.')
    """, (svc_ids[0], carol, alice, 5999))

def notify(db, user_id, title, body, link=None):
    db.execute("INSERT INTO notifications (user_id, title, body, link) VALUES (?, ?, ?, ?)", (user_id, title, body, link))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def seller_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "seller":
            flash("Only sellers can access this page.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if "user_id" in session:
        return {"id": session["user_id"], "name": session["name"], "role": session["role"], "email": session["email"], "is_admin": session.get("is_admin", False)}
    return None

@app.context_processor
def inject_user():
    user = current_user()
    unread_count = 0
    if user:
        with get_db() as db:
            db_user = db.execute("SELECT is_banned FROM users WHERE id=?", (user["id"],)).fetchone()
            if db_user and db_user["is_banned"]:
                session.clear()
                return dict(current_user=None, unread_notifications=0)
            unread_count = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user["id"],)).fetchone()[0]
    return dict(current_user=user, unread_notifications=unread_count)

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            if user["is_banned"]:
                flash("Your account has been suspended.", "danger")
                return render_template("login.html")
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            session["is_admin"] = bool(user["is_admin"])
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "buyer")
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("signup.html")
        if role not in ("buyer", "seller"):
            role = "buyer"
        with get_db() as db:
            existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                flash("An account with this email already exists.", "danger")
                return render_template("signup.html")
            db.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)", (name, email, generate_password_hash(password), role))
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            notify(db, user["id"], "Welcome to FreelanceHub!", f"Hi {name}, your account is ready!", url_for("index"))
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]
        session["email"] = user["email"]
        session["is_admin"] = False
        flash(f"Welcome to FreelanceHub, {name}!", "success")
        return redirect(url_for("index"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/")
def index():
    with get_db() as db:
        categories = db.execute("SELECT c.*, COUNT(s.id) as service_count FROM categories c LEFT JOIN services s ON s.category_id = c.id GROUP BY c.id").fetchall()
        trending = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.is_approved=1 GROUP BY s.id ORDER BY s.view_count DESC LIMIT 4
        """).fetchall()
        featured = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.is_approved=1 GROUP BY s.id ORDER BY s.created_at DESC LIMIT 8
        """).fetchall()
        total_services = db.execute("SELECT COUNT(*) FROM services WHERE is_approved=1").fetchone()[0]
        total_sellers = db.execute("SELECT COUNT(*) FROM users WHERE role='seller'").fetchone()[0]
        total_orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    return render_template("index.html", categories=categories, trending=trending, featured=featured,
                           total_services=total_services, total_sellers=total_sellers, total_orders=total_orders)

@app.route("/browse")
def browse():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", type=int, default=0)
    max_price = request.args.get("max_price", type=int, default=0)
    sort = request.args.get("sort", "newest")
    page = max(1, request.args.get("page", type=int, default=1))
    per_page = 12
    base_query = """SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
               COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
        FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
        LEFT JOIN reviews r ON r.service_id = s.id WHERE s.is_approved=1"""
    count_query = """SELECT COUNT(DISTINCT s.id) FROM services s JOIN categories c ON s.category_id = c.id
        LEFT JOIN reviews r ON r.service_id = s.id WHERE s.is_approved=1"""
    params = []; filters = ""
    if search:
        filters += " AND (s.title LIKE ? OR s.description LIKE ? OR s.tags LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if category:
        filters += " AND c.slug = ?"; params.append(category)
    if min_price > 0:
        filters += " AND s.price >= ?"; params.append(min_price)
    if max_price > 0:
        filters += " AND s.price <= ?"; params.append(max_price)
    order = {"newest": "s.created_at DESC","price_low": "s.price ASC","price_high": "s.price DESC","popular": "s.view_count DESC","top_rated": "avg_rating DESC"}.get(sort, "s.created_at DESC")
    with get_db() as db:
        total = db.execute(count_query + filters, params).fetchone()[0]
        services = db.execute(base_query + filters + f" GROUP BY s.id ORDER BY {order} LIMIT ? OFFSET ?", params + [per_page, (page - 1) * per_page]).fetchall()
        categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template("browse.html", services=services, categories=categories, search=search,
                           selected_category=category, min_price=min_price, max_price=max_price,
                           sort=sort, page=page, total_pages=total_pages, total=total)

@app.route("/services/<int:service_id>")
def service_detail(service_id):
    with get_db() as db:
        service = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug,
                   u.name as seller_name, u.email as seller_email, u.id as seller_user_id,
                   u.created_at as seller_joined, u.bio as seller_bio,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id WHERE s.id = ? GROUP BY s.id
        """, (service_id,)).fetchone()
        if not service:
            flash("Service not found.", "danger")
            return redirect(url_for("browse"))
        db.execute("UPDATE services SET view_count = view_count + 1 WHERE id = ?", (service_id,))
        related = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.category_id = ? AND s.id != ? AND s.is_approved=1
            GROUP BY s.id LIMIT 3
        """, (service["category_id"], service_id)).fetchall()
        reviews = db.execute("""
            SELECT rv.*, u.name as reviewer_name FROM reviews rv JOIN users u ON rv.reviewer_id = u.id
            WHERE rv.service_id = ? ORDER BY rv.created_at DESC
        """, (service_id,)).fetchall()
        user_review = None; can_review = False; existing_inquiry = None; is_saved = False; inquiry_messages = []
        if "user_id" in session:
            user_review = db.execute("SELECT * FROM reviews WHERE service_id=? AND reviewer_id=?", (service_id, session["user_id"])).fetchone()
            has_order = db.execute("SELECT id FROM orders WHERE service_id=? AND buyer_id=? AND status='completed'", (service_id, session["user_id"])).fetchone()
            can_review = bool(has_order) and not user_review
            existing_inquiry = db.execute("SELECT * FROM inquiries WHERE service_id=? AND buyer_id=?", (service_id, session["user_id"])).fetchone()
            is_saved = bool(db.execute("SELECT id FROM saved_services WHERE user_id=? AND service_id=?", (session["user_id"], service_id)).fetchone())
            if existing_inquiry:
                inquiry_messages = db.execute("""
                    SELECT m.*, u.name as sender_name FROM messages m JOIN users u ON m.sender_id=u.id
                    WHERE m.inquiry_id=? ORDER BY m.created_at ASC
                """, (existing_inquiry["id"],)).fetchall()
        seller_order_count = db.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='completed'", (service["seller_id"],)).fetchone()[0]
    tags = json.loads(service["tags"]) if service["tags"] else []
    return render_template("service_detail.html", service=service, related=related, tags=tags,
                           reviews=reviews, user_review=user_review, can_review=can_review,
                           seller_order_count=seller_order_count, existing_inquiry=existing_inquiry,
                           inquiry_messages=inquiry_messages, is_saved=is_saved)

@app.route("/services/<int:service_id>/review", methods=["POST"])
@login_required
def submit_review(service_id):
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()
    if not rating or rating < 1 or rating > 5:
        flash("Please select a valid rating.", "danger")
        return redirect(url_for("service_detail", service_id=service_id))
    with get_db() as db:
        has_order = db.execute("SELECT id FROM orders WHERE service_id=? AND buyer_id=? AND status='completed'", (service_id, session["user_id"])).fetchone()
        if not has_order:
            flash("You can only review services you have purchased and received.", "warning")
            return redirect(url_for("service_detail", service_id=service_id))
        existing = db.execute("SELECT id FROM reviews WHERE service_id=? AND reviewer_id=?", (service_id, session["user_id"])).fetchone()
        if existing:
            flash("You have already reviewed this service.", "warning")
            return redirect(url_for("service_detail", service_id=service_id))
        db.execute("INSERT INTO reviews (service_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)", (service_id, session["user_id"], rating, comment))
        svc = db.execute("SELECT seller_id, title FROM services WHERE id=?", (service_id,)).fetchone()
        notify(db, svc["seller_id"], "New Review Received!", f"{session['name']} left a {rating}-star review on \"{svc['title']}\".", url_for("service_detail", service_id=service_id))
    flash("Review submitted! Thank you.", "success")
    return redirect(url_for("service_detail", service_id=service_id))

@app.route("/services/<int:service_id>/inquire", methods=["POST"])
@login_required
def start_inquiry(service_id):
    if session.get("role") == "seller":
        flash("Sellers cannot send buyer inquiries.", "warning")
        return redirect(url_for("service_detail", service_id=service_id))
    message_text = request.form.get("message", "").strip()
    if not message_text:
        flash("Please write a message.", "danger")
        return redirect(url_for("service_detail", service_id=service_id))
    with get_db() as db:
        service = db.execute("SELECT * FROM services WHERE id=?", (service_id,)).fetchone()
        if not service or service["seller_id"] == session["user_id"]:
            flash("Cannot inquire about this service.", "warning")
            return redirect(url_for("service_detail", service_id=service_id))
        existing = db.execute("SELECT id FROM inquiries WHERE service_id=? AND buyer_id=?", (service_id, session["user_id"])).fetchone()
        if existing:
            inquiry_id = existing["id"]
        else:
            db.execute("INSERT INTO inquiries (service_id, buyer_id, seller_id) VALUES (?, ?, ?)", (service_id, session["user_id"], service["seller_id"]))
            inquiry_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            notify(db, service["seller_id"], "New Inquiry!", f"{session['name']} sent an inquiry about \"{service['title']}\".", url_for("service_detail", service_id=service_id))
        db.execute("INSERT INTO messages (inquiry_id, sender_id, content) VALUES (?, ?, ?)", (inquiry_id, session["user_id"], message_text))
    flash("Message sent to seller!", "success")
    return redirect(url_for("service_detail", service_id=service_id))

@app.route("/services/<int:service_id>/inquiry/reply", methods=["POST"])
@login_required
def reply_inquiry(service_id):
    message_text = request.form.get("message", "").strip()
    if not message_text:
        return redirect(url_for("service_detail", service_id=service_id))
    with get_db() as db:
        inquiry = db.execute("SELECT * FROM inquiries WHERE service_id=? AND (buyer_id=? OR seller_id=?)", (service_id, session["user_id"], session["user_id"])).fetchone()
        if not inquiry:
            flash("Inquiry not found.", "danger")
            return redirect(url_for("service_detail", service_id=service_id))
        db.execute("INSERT INTO messages (inquiry_id, sender_id, content) VALUES (?, ?, ?)", (inquiry["id"], session["user_id"], message_text))
        other_id = inquiry["seller_id"] if session["user_id"] == inquiry["buyer_id"] else inquiry["buyer_id"]
        svc = db.execute("SELECT title FROM services WHERE id=?", (service_id,)).fetchone()
        notify(db, other_id, f"New reply from {session['name']}", f"Reply in inquiry about \"{svc['title']}\".", url_for("service_detail", service_id=service_id))
    flash("Reply sent!", "success")
    return redirect(url_for("service_detail", service_id=service_id))

@app.route("/services/<int:service_id>/save", methods=["POST"])
@login_required
def toggle_save(service_id):
    with get_db() as db:
        existing = db.execute("SELECT id FROM saved_services WHERE user_id=? AND service_id=?", (session["user_id"], service_id)).fetchone()
        if existing:
            db.execute("DELETE FROM saved_services WHERE user_id=? AND service_id=?", (session["user_id"], service_id))
            flash("Removed from saved.", "info")
        else:
            db.execute("INSERT INTO saved_services (user_id, service_id) VALUES (?, ?)", (session["user_id"], service_id))
            flash("Saved to wishlist!", "success")
    return redirect(url_for("service_detail", service_id=service_id))

@app.route("/saved")
@login_required
def saved_services():
    with get_db() as db:
        services = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM saved_services sv JOIN services s ON sv.service_id=s.id
            JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id
            LEFT JOIN reviews r ON r.service_id=s.id
            WHERE sv.user_id=? AND s.is_approved=1
            GROUP BY s.id ORDER BY sv.created_at DESC
        """, (session["user_id"],)).fetchall()
    return render_template("saved.html", services=services)

@app.route("/post-service", methods=["GET", "POST"])
@seller_required
def post_service():
    with get_db() as db:
        categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=int)
        delivery_days = request.form.get("delivery_days", type=int, default=3)
        category_id = request.form.get("category_id", type=int)
        tags_raw = request.form.get("tags", "").strip()
        image_url = request.form.get("image_url", "").strip()
        uploaded_image_url = None
        if "image_file" in request.files:
            f = request.files["image_file"]
            if f and f.filename and allowed_file(f.filename):
                fname = secure_filename(f.filename)
                fname = f"{int(datetime.utcnow().timestamp())}_{fname}"
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                uploaded_image_url = url_for("static", filename=f"uploads/{fname}")
        errors = []
        if len(title) < 5: errors.append("Title must be at least 5 characters.")
        if len(description) < 20: errors.append("Description must be at least 20 characters.")
        if not price or price < 1: errors.append("Price must be at least Rs.1.")
        if not category_id: errors.append("Please select a category.")
        if errors:
            for e in errors: flash(e, "danger")
            return render_template("post_service.html", categories=categories)
        tags = json.dumps([t.strip() for t in tags_raw.split(",") if t.strip()])
        with get_db() as db:
            cat_row = db.execute("SELECT slug FROM categories WHERE id=?", (category_id,)).fetchone()
            cat_slug = cat_row["slug"] if cat_row else ""
            auto_img = get_service_image(title, description, cat_slug)
            final_image = uploaded_image_url or image_url or auto_img
            db.execute("INSERT INTO services (title, description, price, delivery_days, category_id, seller_id, tags, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (title, description, price, delivery_days or 3, category_id, session["user_id"], tags, final_image))
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        flash("Service posted successfully!", "success")
        return redirect(url_for("service_detail", service_id=new_id))
    return render_template("post_service.html", categories=categories)

@app.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@seller_required
def edit_service(service_id):
    with get_db() as db:
        service = db.execute("SELECT * FROM services WHERE id = ? AND seller_id = ?", (service_id, session["user_id"])).fetchone()
        if not service:
            flash("Service not found.", "danger")
            return redirect(url_for("my_services"))
        categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price", type=int)
            delivery_days = request.form.get("delivery_days", type=int, default=3)
            category_id = request.form.get("category_id", type=int)
            tags_raw = request.form.get("tags", "").strip()
            image_url = request.form.get("image_url", "").strip()
            uploaded_image_url = None
            if "image_file" in request.files:
                f = request.files["image_file"]
                if f and f.filename and allowed_file(f.filename):
                    fname = secure_filename(f.filename)
                    fname = f"{int(datetime.utcnow().timestamp())}_{fname}"
                    f.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                    uploaded_image_url = url_for("static", filename=f"uploads/{fname}")
            cat_row = db.execute("SELECT slug FROM categories WHERE id=?", (category_id,)).fetchone()
            cat_slug = cat_row["slug"] if cat_row else ""
            auto_img = get_service_image(title, description, cat_slug)
            final_image = uploaded_image_url or image_url or service["image_url"] or auto_img
            tags = json.dumps([t.strip() for t in tags_raw.split(",") if t.strip()])
            db.execute("UPDATE services SET title=?, description=?, price=?, delivery_days=?, category_id=?, tags=?, image_url=? WHERE id=?",
                       (title, description, price, delivery_days or 3, category_id, tags, final_image, service_id))
            flash("Service updated!", "success")
            return redirect(url_for("service_detail", service_id=service_id))
    tags_str = ", ".join(json.loads(service["tags"])) if service["tags"] else ""
    return render_template("edit_service.html", service=service, categories=categories, tags_str=tags_str)

@app.route("/services/<int:service_id>/delete", methods=["POST"])
@seller_required
def delete_service(service_id):
    with get_db() as db:
        service = db.execute("SELECT id FROM services WHERE id = ? AND seller_id = ?", (service_id, session["user_id"])).fetchone()
        if service:
            db.execute("DELETE FROM services WHERE id = ?", (service_id,))
            flash("Service deleted.", "success")
        else:
            flash("Service not found.", "danger")
    return redirect(url_for("my_services"))

@app.route("/my-services")
@seller_required
def my_services():
    with get_db() as db:
        services = db.execute("""
            SELECT s.*, c.name as category_name,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count,
                   COUNT(DISTINCT o.id) as order_count
            FROM services s JOIN categories c ON s.category_id = c.id
            LEFT JOIN reviews r ON r.service_id = s.id LEFT JOIN orders o ON o.service_id = s.id
            WHERE s.seller_id = ? GROUP BY s.id ORDER BY s.created_at DESC
        """, (session["user_id"],)).fetchall()
        total_views = db.execute("SELECT COALESCE(SUM(view_count),0) FROM services WHERE seller_id=?", (session["user_id"],)).fetchone()[0]
        total_earnings = db.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE seller_id=? AND status='completed'", (session["user_id"],)).fetchone()[0]
        pending_orders = db.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='pending'", (session["user_id"],)).fetchone()[0]
        active_orders = db.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='active'", (session["user_id"],)).fetchone()[0]
    return render_template("my_services.html", services=services, total_views=total_views,
                           total_earnings=total_earnings, pending_orders=pending_orders, active_orders=active_orders)

@app.route("/trending")
def trending():
    with get_db() as db:
        services = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.is_approved=1 GROUP BY s.id ORDER BY s.view_count DESC LIMIT 20
        """).fetchall()
    return render_template("trending.html", services=services)

@app.route("/recommendations")
def recommendations():
    category = request.args.get("category", "")
    with get_db() as db:
        if category:
            services = db.execute("""
                SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                       COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
                FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
                LEFT JOIN reviews r ON r.service_id = s.id
                WHERE c.slug = ? AND s.is_approved=1 GROUP BY s.id ORDER BY s.view_count DESC LIMIT 12
            """, (category,)).fetchall()
        else:
            services = db.execute("""
                SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
                       COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
                FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
                LEFT JOIN reviews r ON r.service_id = s.id
                WHERE s.is_approved=1 GROUP BY s.id ORDER BY RANDOM() LIMIT 12
            """).fetchall()
        categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template("recommendations.html", services=services, categories=categories, selected=category)

@app.route("/services/<int:service_id>/checkout")
@login_required
def checkout(service_id):
    if session.get("role") == "seller":
        with get_db() as db:
            is_own = db.execute("SELECT id FROM services WHERE id=? AND seller_id=?", (service_id, session["user_id"])).fetchone()
        if is_own:
            flash("You cannot purchase your own service.", "warning")
            return redirect(url_for("service_detail", service_id=service_id))
    with get_db() as db:
        service = db.execute("""
            SELECT s.*, c.name as category_name, u.name as seller_name, u.id as seller_user_id
            FROM services s JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id
            WHERE s.id=? AND s.is_approved=1
        """, (service_id,)).fetchone()
        if not service:
            flash("Service not found.", "danger")
            return redirect(url_for("browse"))
        existing_inquiry = db.execute("SELECT * FROM inquiries WHERE service_id=? AND buyer_id=? AND status='open'", (service_id, session["user_id"])).fetchone()
    return render_template("checkout.html", service=service, existing_inquiry=existing_inquiry)

@app.route("/services/<int:service_id>/place-order", methods=["POST"])
@login_required
def place_order(service_id):
    payment_method = request.form.get("payment_method", "")
    notes = request.form.get("notes", "").strip()
    valid_methods = ["upi", "netbanking", "card", "paypal", "bank_transfer", "wallet"]
    if payment_method not in valid_methods:
        flash("Please select a valid payment method.", "danger")
        return redirect(url_for("checkout", service_id=service_id))
    with get_db() as db:
        service = db.execute("SELECT * FROM services WHERE id=? AND is_approved=1", (service_id,)).fetchone()
        if not service:
            flash("Service not found.", "danger")
            return redirect(url_for("browse"))
        payment_ref = f"PAY{random.randint(100000000, 999999999)}"
        db.execute("""INSERT INTO orders (service_id, buyer_id, seller_id, status, payment_method, payment_ref, total_price, notes)
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)""",
            (service_id, session["user_id"], service["seller_id"], payment_method, payment_ref, service["price"], notes))
        order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("UPDATE inquiries SET status='closed' WHERE service_id=? AND buyer_id=?", (service_id, session["user_id"]))
        notify(db, service["seller_id"], "New Order Received!", f"{session['name']} ordered \"{service['title']}\".", url_for("order_detail", order_id=order_id))
        notify(db, session["user_id"], "Order Placed!", f"Your order for \"{service['title']}\". Ref: {payment_ref}", url_for("order_detail", order_id=order_id))
    flash(f"Order placed! Reference: {payment_ref}", "success")
    return redirect(url_for("order_detail", order_id=order_id))

@app.route("/orders")
@login_required
def my_orders():
    with get_db() as db:
        if session.get("role") == "seller":
            orders = db.execute("""SELECT o.*, s.title as service_title, s.image_url, u.name as buyer_name
                FROM orders o JOIN services s ON o.service_id=s.id JOIN users u ON o.buyer_id=u.id
                WHERE o.seller_id=? ORDER BY o.created_at DESC""", (session["user_id"],)).fetchall()
        else:
            orders = db.execute("""SELECT o.*, s.title as service_title, s.image_url, u.name as seller_name
                FROM orders o JOIN services s ON o.service_id=s.id JOIN users u ON o.seller_id=u.id
                WHERE o.buyer_id=? ORDER BY o.created_at DESC""", (session["user_id"],)).fetchall()
    return render_template("orders.html", orders=orders)

@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    with get_db() as db:
        order = db.execute("""
            SELECT o.*, s.title as service_title, s.description as service_desc, s.id as svc_id, s.image_url,
                   buyer.name as buyer_name, seller.name as seller_name, seller.email as seller_email, buyer.email as buyer_email
            FROM orders o JOIN services s ON o.service_id=s.id
            JOIN users buyer ON o.buyer_id=buyer.id JOIN users seller ON o.seller_id=seller.id WHERE o.id=?
        """, (order_id,)).fetchone()
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for("my_orders"))
        if session["user_id"] not in (order["buyer_id"], order["seller_id"]) and not session.get("is_admin"):
            flash("Access denied.", "danger")
            return redirect(url_for("my_orders"))
        messages = db.execute("""SELECT m.*, u.name as sender_name FROM messages m JOIN users u ON m.sender_id=u.id
            WHERE m.order_id=? ORDER BY m.created_at ASC""", (order_id,)).fetchall()
        db.execute("UPDATE messages SET is_read=1 WHERE order_id=? AND sender_id != ?", (order_id, session["user_id"]))
    return render_template("order_detail.html", order=order, messages=messages)

@app.route("/orders/<int:order_id>/update-status", methods=["POST"])
@login_required
def update_order_status(order_id):
    new_status = request.form.get("status", "")
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for("my_orders"))
        uid = session["user_id"]; role = session.get("role"); allowed = False
        if role == "seller" and uid == order["seller_id"]:
            if new_status == "active" and order["status"] == "pending": allowed = True
            elif new_status == "completed" and order["status"] == "active": allowed = True
            elif new_status == "cancelled" and order["status"] == "pending": allowed = True
        if uid == order["buyer_id"]:
            if new_status == "cancelled" and order["status"] == "pending": allowed = True
            elif new_status == "completed" and order["status"] == "active": allowed = True
        if not allowed:
            flash("You cannot perform this action.", "warning")
            return redirect(url_for("order_detail", order_id=order_id))
        db.execute("UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?", (new_status, order_id))
        svc = db.execute("SELECT title FROM services WHERE id=?", (order["service_id"],)).fetchone()
        label = {"active": "Accepted", "completed": "Completed", "cancelled": "Cancelled"}.get(new_status, new_status.title())
        other = order["buyer_id"] if uid == order["seller_id"] else order["seller_id"]
        notify(db, other, f"Order {label}", f"Order for \"{svc['title']}\" is now {label.lower()}.", url_for("order_detail", order_id=order_id))
    flash(f"Order updated to {new_status}.", "success")
    return redirect(url_for("order_detail", order_id=order_id))

@app.route("/orders/<int:order_id>/message", methods=["POST"])
@login_required
def send_message(order_id):
    content = request.form.get("content", "").strip()
    if not content:
        return redirect(url_for("order_detail", order_id=order_id))
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order or session["user_id"] not in (order["buyer_id"], order["seller_id"]):
            flash("Access denied.", "danger")
            return redirect(url_for("my_orders"))
        db.execute("INSERT INTO messages (order_id, sender_id, content) VALUES (?, ?, ?)", (order_id, session["user_id"], content))
        other = order["buyer_id"] if session["user_id"] == order["seller_id"] else order["seller_id"]
        svc = db.execute("SELECT title FROM services WHERE id=?", (order["service_id"],)).fetchone()
        notify(db, other, f"New message from {session['name']}", f"Message about \"{svc['title']}\".", url_for("order_detail", order_id=order_id))
    return redirect(url_for("order_detail", order_id=order_id))

@app.route("/notifications")
@login_required
def notifications():
    with get_db() as db:
        notifs = db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (session["user_id"],)).fetchall()
        db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session["user_id"],))
    return render_template("notifications.html", notifs=notifs)

@app.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_notifications_read():
    with get_db() as db:
        db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session["user_id"],))
    flash("All marked as read.", "success")
    return redirect(url_for("notifications"))

@app.route("/help")
def help_center():
    return render_template("help.html")

@app.route("/support", methods=["GET", "POST"])
def support():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        category = request.form.get("category", "general")
        message = request.form.get("message", "").strip()
        if not name or not email or not subject or not message:
            flash("Please fill in all required fields.", "danger")
            return render_template("support.html")
        priority = "high" if any(w in message.lower() for w in ["urgent", "asap", "immediately", "payment"]) else "normal"
        user_id = session.get("user_id")
        with get_db() as db:
            db.execute("INSERT INTO support_tickets (user_id, name, email, subject, category, message, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (user_id, name, email, subject, category, message, priority))
            ticket_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            if user_id:
                notify(db, user_id, "Support Ticket Created", f"Ticket #{ticket_id} received. We'll respond within 24 hours.", url_for("support"))
        flash(f"Support ticket #{ticket_id} submitted! We'll respond within 24 hours.", "success")
        return redirect(url_for("help_center"))
    user_data = None
    if "user_id" in session:
        with get_db() as db:
            user_data = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("support.html", user_data=user_data)

@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        services = db.execute("""SELECT s.*, c.name as category_name, u.name as seller_name
            FROM services s JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id
            ORDER BY s.created_at DESC""").fetchall()
        orders = db.execute("""SELECT o.*, s.title as service_title, b.name as buyer_name, sl.name as seller_name
            FROM orders o JOIN services s ON o.service_id=s.id
            JOIN users b ON o.buyer_id=b.id JOIN users sl ON o.seller_id=sl.id
            ORDER BY o.created_at DESC LIMIT 20""").fetchall()
        tickets = db.execute("SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 20").fetchall()
        stats = {
            "total_users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "total_services": db.execute("SELECT COUNT(*) FROM services").fetchone()[0],
            "total_orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            "total_revenue": db.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE status='completed'").fetchone()[0],
            "pending_orders": db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0],
            "active_orders": db.execute("SELECT COUNT(*) FROM orders WHERE status='active'").fetchone()[0],
            "open_tickets": db.execute("SELECT COUNT(*) FROM support_tickets WHERE status='open'").fetchone()[0],
        }
    return render_template("admin.html", users=users, services=services, orders=orders, stats=stats, tickets=tickets)

@app.route("/admin/users/<int:user_id>/ban", methods=["POST"])
@admin_required
def admin_ban_user(user_id):
    action = request.form.get("action", "ban")
    with get_db() as db:
        if action == "ban":
            db.execute("UPDATE users SET is_banned=1 WHERE id=?", (user_id,))
            flash("User banned.", "warning")
        else:
            db.execute("UPDATE users SET is_banned=0 WHERE id=?", (user_id,))
            flash("User unbanned.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/services/<int:service_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_service(service_id):
    with get_db() as db:
        svc = db.execute("SELECT is_approved FROM services WHERE id=?", (service_id,)).fetchone()
        if svc:
            new_val = 0 if svc["is_approved"] else 1
            db.execute("UPDATE services SET is_approved=? WHERE id=?", (new_val, service_id))
            flash("Service " + ("approved." if new_val else "hidden."), "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/services/<int:service_id>/delete", methods=["POST"])
@admin_required
def admin_delete_service(service_id):
    with get_db() as db:
        db.execute("DELETE FROM services WHERE id=?", (service_id,))
    flash("Service deleted.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/tickets/<int:ticket_id>/reply", methods=["POST"])
@admin_required
def admin_reply_ticket(ticket_id):
    reply = request.form.get("reply", "").strip()
    status = request.form.get("status", "open")
    if reply:
        with get_db() as db:
            ticket = db.execute("SELECT * FROM support_tickets WHERE id=?", (ticket_id,)).fetchone()
            if ticket:
                db.execute("UPDATE support_tickets SET admin_reply=?, status=?, updated_at=datetime('now') WHERE id=?", (reply, status, ticket_id))
                if ticket["user_id"]:
                    notify(db, ticket["user_id"], f"Support Reply #{ticket_id}", reply[:80], url_for("support"))
        flash("Reply sent.", "success")
    return redirect(url_for("admin_dashboard"))

CATEGORY_KEYWORDS = {
    "design": ["logo","design","brand","graphic","ui","ux","illustrat","banner","flyer","poster","icon","visual"],
    "development": ["web","app","code","develop","program","software","website","react","python","flutter","mobile","api"],
    "writing": ["write","blog","article","content","copy","essay","edit","proofread","translat","script"],
    "marketing": ["seo","social media","market","ads","advertis","email","campaign","google","facebook","instagram"],
    "video": ["video","edit","animat","youtube","film","motion","reel","vlog"],
    "music": ["music","audio","voice","sound","record","mix","master","podcast","jingle"],
    "data": ["data","excel","analytic","dashboard","chart","sql","tableau","power bi","python","scraping"],
    "business": ["business","plan","consult","strateg","financ","account","pitch","startup","market research"],
}

@app.route("/api/suggest-price")
def api_suggest_price():
    category = request.args.get("category", "")
    with get_db() as db:
        cat_row = db.execute("SELECT slug FROM categories WHERE id=?", (category,)).fetchone()
        slug = cat_row["slug"] if cat_row else ""
        sample = db.execute("SELECT AVG(price) as avg, MIN(price) as mn, MAX(price) as mx, COUNT(*) as cnt FROM services WHERE category_id=?", (category,)).fetchone()
    PRICE_RANGES = {"design":{"min":2000,"max":50000,"avg":12000},"development":{"min":8000,"max":150000,"avg":35000},"writing":{"min":500,"max":15000,"avg":4000},"marketing":{"min":3000,"max":80000,"avg":18000},"video":{"min":2000,"max":60000,"avg":12000},"music":{"min":1000,"max":20000,"avg":6000},"data":{"min":3000,"max":40000,"avg":10000},"business":{"min":5000,"max":100000,"avg":20000}}
    ranges = PRICE_RANGES.get(slug, {"min":1000,"max":50000,"avg":10000})
    if sample["cnt"] and sample["cnt"] > 0:
        suggested = int(sample["avg"]); mn = int(sample["mn"]); mx = int(sample["mx"]); msg = f"Based on {sample['cnt']} similar services"
    else:
        suggested = ranges["avg"]; mn = ranges["min"]; mx = ranges["max"]; msg = "Based on market norms"
    return jsonify({"suggested": max(1, suggested + random.randint(-500,500)), "min": mn, "max": mx, "message": msg})

@app.route("/api/auto-categorize")
def api_auto_categorize():
    text = (request.args.get("title","") + " " + request.args.get("description","")).lower()
    best_slug, best_score = "design", 0
    for slug, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score: best_score, best_slug = score, slug
    with get_db() as db:
        cat = db.execute("SELECT * FROM categories WHERE slug=?", (best_slug,)).fetchone()
    return jsonify({"category_id": cat["id"], "category_name": cat["name"], "slug": best_slug, "confidence": min(0.95, 0.5+best_score*0.1)})

@app.route("/api/search-autocomplete")
def api_search_autocomplete():
    q = request.args.get("q","").strip()
    if len(q) < 2: return jsonify([])
    with get_db() as db:
        results = db.execute("""SELECT s.id, s.title, c.name as category_name, s.price
            FROM services s JOIN categories c ON s.category_id=c.id
            WHERE s.is_approved=1 AND (s.title LIKE ? OR s.tags LIKE ?)
            ORDER BY s.view_count DESC LIMIT 7""", (f"%{q}%", f"%{q}%")).fetchall()
    return jsonify([{"id":r["id"],"title":r["title"],"category":r["category_name"],"price":r["price"]} for r in results])

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message","").strip()
    message_lower = message.lower()
    with get_db() as db:
        services = []; reply = ""; suggestions = []
        found_slug = None
        for slug, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords): found_slug = slug; break
        words = re.findall(r'\w+', message_lower)
        stop = {"need","want","looking","find","help","best","good","cheap","fast","quick","please","show","give","list","some","can","you","what","how","tell","about","more","with","have","does","this","that","for","the","and","but","not","are","from","they","will","been","your","when","also","into","than","then","just","like","over","only","most","after","before","should","would","could","which","there","hello","hey","hi","thanks","thank"}
        search_terms = [w for w in words if len(w) > 3 and w not in stop]
        if search_terms:
            like_clauses = " OR ".join(["(s.title LIKE ? OR s.tags LIKE ?)"] * len(search_terms))
            params = []
            for t in search_terms: params += [f"%{t}%", f"%{t}%"]
            services = db.execute(f"""SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, COALESCE(AVG(r.rating),0) as avg_rating
                FROM services s JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id LEFT JOIN reviews r ON r.service_id=s.id
                WHERE s.is_approved=1 AND ({like_clauses}) GROUP BY s.id ORDER BY s.view_count DESC LIMIT 4""", params).fetchall()
        if not services and found_slug:
            services = db.execute("""SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, COALESCE(AVG(r.rating),0) as avg_rating
                FROM services s JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id LEFT JOIN reviews r ON r.service_id=s.id
                WHERE s.is_approved=1 AND c.slug=? GROUP BY s.id ORDER BY s.view_count DESC LIMIT 4""", (found_slug,)).fetchall()

        greetings = ["hi","hello","hey","greetings"]
        if any(g in message_lower for g in greetings):
            reply = "Hey there! I'm your FreelanceHub AI assistant. What kind of service are you looking for today?"
            suggestions = ["Find a logo designer","I need a website","Content writing services","How do I place an order?"]
        elif services:
            reply = f"I found {len(services)} service{'s' if len(services)>1 else ''} matching your needs:"
        elif any(w in message_lower for w in ["price","cost","how much","budget"]):
            reply = "Pricing varies by category: Design (Rs.2K–50K), Development (Rs.8K–1.5L), Writing (Rs.500–15K), Marketing (Rs.3K–80K). Use Browse filters to set your budget!"
            suggestions = ["Browse by price","Affordable services","Premium services"]
        elif any(w in message_lower for w in ["sell","post","offer","become seller"]):
            reply = "Becoming a seller is free! Sign up with 'Seller' role, then go to 'Post a Service'. Our AI suggests optimal pricing based on market data."
            suggestions = ["Sign up as seller","View trending services"]
        elif any(w in message_lower for w in ["order","buy","purchase","hire"]):
            reply = "To place an order: Browse → Click a service → Message the seller to discuss → Confirm & pay. A private chat opens after payment for all future communication!"
            suggestions = ["Browse services","How does messaging work?"]
        elif any(w in message_lower for w in ["payment","pay","upi","card"]):
            reply = "We accept: UPI, Credit/Debit Cards, Net Banking, PayPal, Bank Transfer, and Digital Wallets. All payments are secured with 256-bit encryption."
        elif any(w in message_lower for w in ["contact","message","chat","communicate"]):
            reply = "Use 'Message Seller' on any service page for pre-purchase queries. After ordering, a private chat opens automatically — all on-platform for safety!"
        elif any(w in message_lower for w in ["support","help","problem","issue"]):
            reply = "Need help? Visit our Help Center for guides, or submit a Support Ticket for personalised assistance. We respond within 24 hours!"
            suggestions = ["Go to Help Center","Submit a ticket"]
        elif any(w in message_lower for w in ["refund","cancel","dispute"]):
            reply = "For cancellations: request from Orders page while status is Pending. For disputes, contact our support team via Help Center."
        else:
            reply = "I'm here to help! Try asking 'I need a logo', 'looking for web developers', or 'how does payment work'."
            suggestions = ["Browse all services","What's trending?","How does FreelanceHub work?"]

    services_list = [{"id":s["id"],"title":s["title"],"price":s["price"],"seller":s["seller_name"],"category":s["category_name"],"rating":round(float(s["avg_rating"]),1),"image":s["image_url"] or CATEGORY_DEFAULT_IMAGES.get(s["category_slug"],"")} for s in services]
    return jsonify({"reply": reply, "services": services_list, "suggestions": suggestions})

@app.route("/profile/<int:user_id>")
def profile(user_id):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("index"))
        services = db.execute("""SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name,
               COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.seller_id=? AND s.is_approved=1 GROUP BY s.id ORDER BY s.created_at DESC""", (user_id,)).fetchall()
        completed_orders = db.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='completed'", (user_id,)).fetchone()[0]
        avg_rating = db.execute("SELECT COALESCE(AVG(r.rating),0) FROM reviews r JOIN services s ON r.service_id=s.id WHERE s.seller_id=?", (user_id,)).fetchone()[0]
        review_count = db.execute("SELECT COUNT(*) FROM reviews r JOIN services s ON r.service_id=s.id WHERE s.seller_id=?", (user_id,)).fetchone()[0]
        recent_reviews = db.execute("""SELECT rv.*, u.name as reviewer_name, s.title as service_title
            FROM reviews rv JOIN users u ON rv.reviewer_id = u.id JOIN services s ON rv.service_id = s.id
            WHERE s.seller_id=? ORDER BY rv.created_at DESC LIMIT 6""", (user_id,)).fetchall()
    return render_template("profile.html", profile_user=user, services=services,
                           completed_orders=completed_orders, avg_rating=avg_rating,
                           review_count=review_count, recent_reviews=recent_reviews)

@app.route("/account", methods=["GET","POST"])
@login_required
def account():
    if request.method == "POST":
        action = request.form.get("action","profile")
        with get_db() as db:
            if action == "profile":
                name = request.form.get("name","").strip()
                bio = request.form.get("bio","").strip()
                location = request.form.get("location","").strip()
                website = request.form.get("website","").strip()
                if not name:
                    flash("Name cannot be empty.", "danger")
                    return redirect(url_for("account"))
                db.execute("UPDATE users SET name=?, bio=?, location=?, website=? WHERE id=?", (name, bio, location, website, session["user_id"]))
                session["name"] = name
                flash("Profile updated!", "success")
            elif action == "password":
                current_pw = request.form.get("current_password","")
                new_pw = request.form.get("new_password","")
                confirm_pw = request.form.get("confirm_password","")
                user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
                if not check_password_hash(user["password_hash"], current_pw):
                    flash("Current password incorrect.", "danger"); return redirect(url_for("account"))
                if len(new_pw) < 6:
                    flash("Password must be 6+ characters.", "danger"); return redirect(url_for("account"))
                if new_pw != confirm_pw:
                    flash("Passwords don't match.", "danger"); return redirect(url_for("account"))
                db.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_pw), session["user_id"]))
                flash("Password changed!", "success")
        return redirect(url_for("account"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("account.html", user=user)

@app.template_filter("inr")
def inr_format(value):
    try: return f"Rs.{int(value):,}"
    except: return f"Rs.{value}"

@app.template_filter("from_json")
def from_json_filter(value):
    try: return json.loads(value) if value else []
    except: return []

@app.template_filter("time_ago")
def time_ago(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        diff = datetime.utcnow() - dt
        days = diff.days; seconds = diff.seconds
        if days == 0:
            if seconds < 60: return "Just now"
            if seconds < 3600: return f"{seconds//60}m ago"
            return f"{seconds//3600}h ago"
        if days == 1: return "Yesterday"
        if days < 30: return f"{days} days ago"
        if days < 365: return f"{days//30} months ago"
        return f"{days//365} years ago"
    except: return dt_str

@app.template_filter("stars")
def stars_filter(value):
    try:
        v = round(float(value))
        return "★" * v + "☆" * (5-v)
    except: return "☆" * 5

@app.template_filter("payment_label")
def payment_label(method):
    labels = {"upi":"UPI","netbanking":"Net Banking","card":"Credit / Debit Card","paypal":"PayPal","bank_transfer":"Bank Transfer","wallet":"Digital Wallet"}
    return labels.get(method, method.title() if method else "—")

# Always initialise the database — works with both gunicorn and direct run
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG","false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
