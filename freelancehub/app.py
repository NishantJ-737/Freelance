from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, re, random, json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "freelancehub-dev-secret-change-in-production")
DATABASE = os.path.join(os.path.dirname(__file__), "freelancehub.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)

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
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def ensure_columns(db):
    """Lightweight schema migrations for existing SQLite files."""
    migrations = [
        "ALTER TABLE users ADD COLUMN is_deleted INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN deleted_at TEXT",
        "ALTER TABLE users ADD COLUMN is_available INTEGER DEFAULT 1",
        "ALTER TABLE users ADD COLUMN available_from TEXT",
        "ALTER TABLE inquiries ADD COLUMN seller_deleted INTEGER DEFAULT 0",
        "ALTER TABLE inquiries ADD COLUMN deleted_at TEXT",
        "ALTER TABLE orders ADD COLUMN revision_notes TEXT",
        "ALTER TABLE orders ADD COLUMN revision_requested_at TEXT",
        "ALTER TABLE orders ADD COLUMN package_id INTEGER",
        "ALTER TABLE services ADD COLUMN packages TEXT",
    ]
    for sql in migrations:
        try:
            db.execute(sql)
        except Exception:
            pass

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
            CREATE TABLE IF NOT EXISTS service_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS custom_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inquiry_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                price INTEGER NOT NULL,
                delivery_days INTEGER NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (inquiry_id) REFERENCES inquiries(id),
                FOREIGN KEY (seller_id) REFERENCES users(id),
                FOREIGN KEY (buyer_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS buyer_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                budget INTEGER DEFAULT 0,
                category_id INTEGER,
                buyer_id INTEGER NOT NULL,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (buyer_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                price INTEGER NOT NULL,
                delivery_days INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (request_id) REFERENCES buyer_requests(id),
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );
        """)
        ensure_columns(db)
        seed_data(db)

def seed_data(db):
    # Seed only once for categories; services/users can be expanded if sparse.
    count = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
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
    if count == 0:
        db.executemany("INSERT INTO categories (name, slug, icon, description) VALUES (?, ?, ?, ?)", categories)

    # Ensure demo/admin users exist (but admin credentials are not shown in UI/README)
    admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
    db.execute(
        "INSERT OR IGNORE INTO users (name, email, password_hash, role, is_admin, avatar_url) VALUES (?, ?, ?, ?, ?, ?)",
        ("Admin User", "admin@freelancehub.com", generate_password_hash(admin_pw), "seller", 1, "https://i.pravatar.cc/150?img=12"),
    )

    # Make demo accounts Indian + unique avatars (no duplicates)
    demo_pw = "password123"
    demo_users = [
        ("Aarav Sharma", "alice@demo.com", "seller", "https://i.pravatar.cc/150?img=21"),
        ("Ishaan Patel", "bob@demo.com", "seller", "https://i.pravatar.cc/150?img=22"),
        ("Vivaan Nair", "david@demo.com", "seller", "https://i.pravatar.cc/150?img=23"),
        ("Ananya Iyer", "carol@demo.com", "buyer", "https://i.pravatar.cc/150?img=31"),
    ]
    for name, email, role, avatar in demo_users:
        db.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role, is_admin, avatar_url) VALUES (?, ?, ?, ?, 0, ?)",
            (name, email, generate_password_hash(demo_pw), role, avatar),
        )

    # 10 explicit seller demo accounts so any random service can be tested live.
    seller_demo = [
        ("Riya Singh", "seller1@demo.com", "https://i.pravatar.cc/150?img=40"),
        ("Saanvi Gupta", "seller2@demo.com", "https://i.pravatar.cc/150?img=41"),
        ("Diya Joshi", "seller3@demo.com", "https://i.pravatar.cc/150?img=42"),
        ("Meera Kapoor", "seller4@demo.com", "https://i.pravatar.cc/150?img=43"),
        ("Aditi Verma", "seller5@demo.com", "https://i.pravatar.cc/150?img=44"),
        ("Arjun Mehta", "seller6@demo.com", "https://i.pravatar.cc/150?img=45"),
        ("Krishna Menon", "seller7@demo.com", "https://i.pravatar.cc/150?img=46"),
        ("Rohit Malhotra", "seller8@demo.com", "https://i.pravatar.cc/150?img=47"),
        ("Aditya Rao", "seller9@demo.com", "https://i.pravatar.cc/150?img=48"),
        ("Nikhil Yadav", "seller10@demo.com", "https://i.pravatar.cc/150?img=49"),
    ]
    for name, email, avatar in seller_demo:
        db.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role, is_admin, avatar_url) VALUES (?, ?, ?, 'seller', 0, ?)",
            (name, email, generate_password_hash(demo_pw), avatar),
        )

    cat = {row["slug"]: row["id"] for row in db.execute("SELECT id, slug FROM categories")}

    # If services are too few, top-up to ~180.
    existing_services = db.execute("SELECT COUNT(*) FROM services").fetchone()[0]
    target_services = 180
    if existing_services < target_services:
        # Get seller ids (exclude admin)
        seller_rows = db.execute("""
            SELECT id
            FROM users
            WHERE role='seller'
              AND email LIKE 'seller%@demo.com'
              AND COALESCE(is_deleted,0)=0
              AND COALESCE(is_banned,0)=0
              AND COALESCE(is_admin,0)=0
            ORDER BY id
        """).fetchall()
        seller_ids = [r["id"] for r in seller_rows] or [db.execute("SELECT id FROM users WHERE email='alice@demo.com'").fetchone()["id"]]

        # Deterministic random for repeatable demo
        rng = random.Random(20260510)

        templates = {
            "design": [
                ("Premium Logo Design for Indian Brands", ["logo","branding","vector"]),
                ("Instagram Post & Story Pack", ["social","design","posts"]),
                ("Modern UI/UX for Mobile App", ["ui","ux","app"]),
                ("Business Card + Letterhead Set", ["stationery","brand"]),
                ("YouTube Thumbnail Bundle", ["youtube","thumbnail","design"]),
            ],
            "development": [
                ("React Website (Landing + Contact Form)", ["react","web","responsive"]),
                ("WordPress Business Website Setup", ["wordpress","cms","website"]),
                ("Flask API Backend + SQLite", ["python","api","flask"]),
                ("E‑commerce Store (Basic)", ["ecommerce","web","payments"]),
                ("Bug Fixing & Performance Optimisation", ["debug","performance","web"]),
            ],
            "writing": [
                ("SEO Blog Article (1000–1500 words)", ["seo","blog","content"]),
                ("Product Descriptions for Store", ["copy","product","ecommerce"]),
                ("Resume / CV Writing (ATS Friendly)", ["resume","career","ats"]),
                ("YouTube Script Writing", ["script","youtube","writing"]),
                ("Proofreading & Editing", ["edit","grammar","writing"]),
            ],
            "marketing": [
                ("Instagram Growth Strategy (30 days)", ["instagram","strategy","growth"]),
                ("Google Ads Setup + Optimisation", ["ads","google","ppc"]),
                ("SEO Audit + Keyword Research", ["seo","audit","keywords"]),
                ("Email Marketing Campaign", ["email","campaign","marketing"]),
                ("LinkedIn Personal Branding", ["linkedin","branding","b2b"]),
            ],
            "video": [
                ("Reels/Shorts Video Editing", ["reels","shorts","edit"]),
                ("YouTube Video Editing (5–10 min)", ["youtube","editing","video"]),
                ("Motion Graphics Intro (5 sec)", ["motion","intro","video"]),
                ("Colour Grading + Sound Mix", ["color","audio","post"]),
                ("Wedding Highlight Edit", ["wedding","edit","video"]),
            ],
            "music": [
                ("Hindi/English Voice Over", ["voice","narration","audio"]),
                ("Podcast Audio Cleanup", ["podcast","audio","noise"]),
                ("Jingle / Brand Sonic Logo", ["jingle","brand","music"]),
                ("Background Music for Videos", ["music","background","video"]),
                ("Audio Mixing & Mastering", ["mix","master","audio"]),
            ],
            "data": [
                ("Excel Dashboard + KPI Tracking", ["excel","dashboard","kpi"]),
                ("Data Cleaning in Python", ["python","data","cleaning"]),
                ("Power BI Report", ["powerbi","bi","report"]),
                ("Web Scraping (Basic)", ["scraping","python","data"]),
                ("SQL Query Optimisation", ["sql","database","tuning"]),
            ],
            "business": [
                ("Investor Pitch Deck (10 slides)", ["pitch","deck","startup"]),
                ("Business Plan for Indian Market", ["business","plan","india"]),
                ("Financial Model (Basic)", ["finance","model","excel"]),
                ("Market Research Report", ["research","market","analysis"]),
                ("Startup Consulting Session (60 min)", ["consulting","startup","strategy"]),
            ],
        }

        unsplash_by_cat = {
            "design": [
                "https://images.unsplash.com/photo-1558655146-364adaf1fcc9?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1634084462412-b54873c0a56d?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800&h=500&fit=crop",
            ],
            "development": [
                "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1518773553398-650c184e0bb3?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=500&fit=crop",
            ],
            "writing": [
                "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1456324504439-367cee3b3c32?w=800&h=500&fit=crop",
            ],
            "marketing": [
                "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=800&h=500&fit=crop",
            ],
            "video": [
                "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1524253482453-3fed8d2fe12b?w=800&h=500&fit=crop",
            ],
            "music": [
                "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=800&h=500&fit=crop",
            ],
            "data": [
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800&h=500&fit=crop",
            ],
            "business": [
                "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=500&fit=crop",
                "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=800&h=500&fit=crop",
            ],
        }

        def make_desc(title, slug):
            base = [
                "Clear communication and fast delivery.",
                "Premium quality tailored for Indian clients.",
                "Includes revisions and helpful guidance.",
                "Professional workflow with timely updates.",
            ]
            return (
                f"{title}\n\n"
                f"{rng.choice(base)} {rng.choice(base)}\n\n"
                "What you get:\n"
                "- Requirement discussion\n"
                "- High quality deliverable\n"
                "- Support after delivery\n"
            )

        to_add = target_services - existing_services
        rows = []
        slugs = list(templates.keys())
        for i in range(to_add):
            slug = slugs[i % len(slugs)]
            title_base, tags_list = rng.choice(templates[slug])
            city = rng.choice(["Mumbai","Delhi","Bengaluru","Hyderabad","Pune","Chennai","Kolkata","Ahmedabad","Jaipur","Lucknow"])
            title = f"{title_base} ({city})"
            desc = make_desc(title_base, slug)
            price = int(rng.randint(499, 5999) if slug == "writing" else rng.randint(1999, 49999))
            delivery = int(rng.randint(1, 10))
            category_id = cat[slug]
            seller_id = rng.choice(seller_ids)
            tags = json.dumps(tags_list)
            img = rng.choice(unsplash_by_cat.get(slug, [CATEGORY_DEFAULT_IMAGES.get(slug)]))
            views = int(rng.randint(10, 1500))
            rows.append((title, desc, price, delivery, category_id, seller_id, tags, img, views))

        db.executemany(
            "INSERT INTO services (title, description, price, delivery_days, category_id, seller_id, tags, image_url, view_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    # Improve older seeded data where all same-category services had same image.
    for slug, img_list in {
        "design": [
            "https://images.unsplash.com/photo-1558655146-364adaf1fcc9?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1634084462412-b54873c0a56d?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800&h=500&fit=crop",
        ],
        "development": [
            "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1518773553398-650c184e0bb3?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=500&fit=crop",
        ],
        "writing": [
            "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1456324504439-367cee3b3c32?w=800&h=500&fit=crop",
        ],
        "marketing": [
            "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=800&h=500&fit=crop",
        ],
        "video": [
            "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1524253482453-3fed8d2fe12b?w=800&h=500&fit=crop",
        ],
        "music": [
            "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=800&h=500&fit=crop",
        ],
        "data": [
            "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800&h=500&fit=crop",
        ],
        "business": [
            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=500&fit=crop",
            "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=800&h=500&fit=crop",
        ],
    }.items():
        cat_row = db.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()
        if not cat_row:
            continue
        svc_rows = db.execute("SELECT id FROM services WHERE category_id=? ORDER BY id", (cat_row["id"],)).fetchall()
        for idx, srow in enumerate(svc_rows):
            db.execute("UPDATE services SET image_url=? WHERE id=?", (img_list[idx % len(img_list)], srow["id"]))

def notify(db, user_id, title, body, link=None):
    db.execute("INSERT INTO notifications (user_id, title, body, link) VALUES (?, ?, ?, ?)", (user_id, title, body, link))

def get_seller_level(completed_orders, avg_rating):
    """Return (label, icon, color) based on seller stats."""
    r = float(avg_rating or 0)
    c = int(completed_orders or 0)
    if c >= 50 and r >= 4.8:
        return ("Elite Pro", "bi-patch-check-fill", "#f5a623")
    if c >= 20 and r >= 4.5:
        return ("Top Seller", "bi-award-fill", "#6c63ff")
    if c >= 5 and r >= 4.0:
        return ("Rising Talent", "bi-graph-up-arrow", "#43d9ad")
    return ("New Seller", "bi-person-circle", "#888")

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
    unread_inquiries = 0
    if user:
        with get_db() as db:
            db_user = db.execute("SELECT is_banned, COALESCE(is_deleted,0) as is_deleted FROM users WHERE id=?", (user["id"],)).fetchone()
            if db_user and (db_user["is_banned"] or db_user["is_deleted"]):
                session.clear()
                return dict(current_user=None, unread_notifications=0, unread_inquiries=0)
            unread_count = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user["id"],)).fetchone()[0]
            unread_inquiries = db.execute("""
                SELECT COUNT(DISTINCT i.id)
                FROM inquiries i
                JOIN messages m ON m.inquiry_id = i.id
                WHERE (i.seller_id=? OR i.buyer_id=?)
                  AND i.status='open'
                  AND (CASE WHEN i.seller_id=? THEN COALESCE(i.seller_deleted,0)=0 ELSE 1 END)
                  AND m.sender_id != ?
                  AND COALESCE(m.is_read,0)=0
            """, (user["id"], user["id"], user["id"], user["id"])).fetchone()[0]
    return dict(current_user=user, unread_notifications=unread_count, unread_inquiries=unread_inquiries)

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ? AND COALESCE(is_deleted,0)=0", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            if user["is_banned"]:
                flash("Your account has been suspended.", "danger")
                return render_template("login.html")
            session["user_id"] = user["id"]
            session.permanent = True
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
            existing = db.execute("SELECT id FROM users WHERE email = ? AND COALESCE(is_deleted,0)=0", (email,)).fetchone()
            if existing:
                flash("An account with this email already exists.", "danger")
                return render_template("signup.html")
            db.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)", (name, email, generate_password_hash(password), role))
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            notify(db, user["id"], "Welcome to FreelanceHub!", f"Hi {name}, your account is ready!", url_for("index"))
        session["user_id"] = user["id"]
        session.permanent = True
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
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, u.avatar_url as seller_avatar,
                   COALESCE(u.is_available,1) as is_available,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.is_approved=1 GROUP BY s.id ORDER BY s.view_count DESC LIMIT 4
        """).fetchall()
        featured = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, u.avatar_url as seller_avatar,
                   COALESCE(u.is_available,1) as is_available,
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
    base_query = """SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, u.avatar_url as seller_avatar,
               COALESCE(u.is_available,1) as is_available,
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
                   u.name as seller_name, u.email as seller_email, u.avatar_url as seller_avatar, u.id as seller_user_id,
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
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, u.avatar_url as seller_avatar,
                   COALESCE(u.is_available,1) as is_available,
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
            existing_inquiry = db.execute("""
                SELECT * FROM inquiries
                WHERE service_id=? AND buyer_id=? AND status='open' AND COALESCE(seller_deleted,0)=0
                ORDER BY id DESC LIMIT 1
            """, (service_id, session["user_id"])).fetchone()
            is_saved = bool(db.execute("SELECT id FROM saved_services WHERE user_id=? AND service_id=?", (session["user_id"], service_id)).fetchone())
            if existing_inquiry:
                inquiry_messages = db.execute("""
                    SELECT m.*, u.name as sender_name FROM messages m JOIN users u ON m.sender_id=u.id
                    WHERE m.inquiry_id=? ORDER BY m.created_at ASC
                """, (existing_inquiry["id"],)).fetchall()
        seller_order_count = db.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='completed'", (service["seller_id"],)).fetchone()[0]
        seller_avg_rating = db.execute("SELECT COALESCE(AVG(r.rating),0) FROM reviews r JOIN services s ON r.service_id=s.id WHERE s.seller_id=?", (service["seller_id"],)).fetchone()[0]
        seller_level = get_seller_level(seller_order_count, seller_avg_rating)
        faqs = db.execute("SELECT * FROM service_faqs WHERE service_id=? ORDER BY sort_order, id", (service_id,)).fetchall()
        packages = json.loads(service["packages"]) if service.get("packages") else []
        custom_offer = None
        if "user_id" in session and existing_inquiry:
            custom_offer = db.execute(
                "SELECT * FROM custom_offers WHERE inquiry_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
                (existing_inquiry["id"],)
            ).fetchone()
    tags = json.loads(service["tags"]) if service["tags"] else []
    return render_template("service_detail.html", service=service, related=related, tags=tags,
                           reviews=reviews, user_review=user_review, can_review=can_review,
                           seller_order_count=seller_order_count, existing_inquiry=existing_inquiry,
                           inquiry_messages=inquiry_messages, is_saved=is_saved,
                           seller_level=seller_level, faqs=faqs, packages=packages,
                           custom_offer=custom_offer)

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
        existing = db.execute("""
            SELECT * FROM inquiries
            WHERE service_id=? AND buyer_id=? AND status='open'
            ORDER BY id DESC LIMIT 1
        """, (service_id, session["user_id"])).fetchone()

        # If seller previously deleted/closed the conversation, start a new one.
        if existing and (int(existing["seller_deleted"] or 0) == 0):
            inquiry_id = existing["id"]
        else:
            db.execute("INSERT INTO inquiries (service_id, buyer_id, seller_id, status, seller_deleted) VALUES (?, ?, ?, 'open', 0)", (service_id, session["user_id"], service["seller_id"]))
            inquiry_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        db.execute("INSERT INTO messages (inquiry_id, sender_id, content) VALUES (?, ?, ?)", (inquiry_id, session["user_id"], message_text))

        notify(
            db,
            service["seller_id"],
            "New Inquiry!",
            f"{session['name']} sent an inquiry about \"{service['title']}\".",
            url_for("inquiry_detail", inquiry_id=inquiry_id),
        )
    flash("Message sent to seller!", "success")
    return redirect(url_for("service_detail", service_id=service_id))

@app.route("/services/<int:service_id>/inquiry/reply", methods=["POST"])
@login_required
def reply_inquiry(service_id):
    message_text = request.form.get("message", "").strip()
    if not message_text:
        return redirect(url_for("service_detail", service_id=service_id))
    with get_db() as db:
        inquiry = db.execute("""
            SELECT * FROM inquiries
            WHERE service_id=? AND status='open' AND (buyer_id=? OR seller_id=?)
            ORDER BY id DESC LIMIT 1
        """, (service_id, session["user_id"], session["user_id"])).fetchone()
        if not inquiry:
            flash("Inquiry not found.", "danger")
            return redirect(url_for("service_detail", service_id=service_id))
        # If seller deleted the thread, buyer must start a new inquiry.
        if int(inquiry["seller_deleted"] or 0) and session["user_id"] == inquiry["buyer_id"]:
            flash("This conversation was closed by the seller. Please start a new inquiry.", "warning")
            return redirect(url_for("service_detail", service_id=service_id))
        db.execute("INSERT INTO messages (inquiry_id, sender_id, content) VALUES (?, ?, ?)", (inquiry["id"], session["user_id"], message_text))
        other_id = inquiry["seller_id"] if session["user_id"] == inquiry["buyer_id"] else inquiry["buyer_id"]
        svc = db.execute("SELECT title FROM services WHERE id=?", (service_id,)).fetchone()
        notify(db, other_id, f"New reply from {session['name']}", f"Reply in inquiry about \"{svc['title']}\".", url_for("inquiry_detail", inquiry_id=inquiry["id"]))
    flash("Reply sent!", "success")
    return redirect(url_for("service_detail", service_id=service_id))

@app.route("/inquiries")
@login_required
def inquiries():
    q = request.args.get("q", "").strip()
    with get_db() as db:
        params = [session["user_id"], session["user_id"], session["user_id"]]
        search_sql = ""
        if q:
            search_sql = " AND (s.title LIKE ? OR b.name LIKE ? OR sl.name LIKE ?)"
            like_q = f"%{q}%"
            params.extend([like_q, like_q, like_q])
        rows = db.execute("""
            SELECT i.*, s.title as service_title, s.image_url as service_image,
                   b.name as buyer_name, sl.name as seller_name,
                   COALESCE(b.is_deleted,0) as buyer_deleted,
                   lm.created_at as last_message_at
            FROM inquiries i
            JOIN services s ON i.service_id=s.id
            JOIN users b ON i.buyer_id=b.id
            JOIN users sl ON i.seller_id=sl.id
            LEFT JOIN (
                SELECT inquiry_id, MAX(created_at) as created_at
                FROM messages
                GROUP BY inquiry_id
            ) lm ON lm.inquiry_id = i.id
            WHERE i.status='open'
              AND (i.buyer_id=? OR i.seller_id=?)
              AND (CASE WHEN i.seller_id=? THEN COALESCE(i.seller_deleted,0)=0 ELSE 1 END)
        """ + search_sql + """
            ORDER BY COALESCE(lm.created_at, i.created_at) DESC, i.id DESC
        """, params).fetchall()
    return render_template("inquiries.html", inquiries=rows, q=q)

@app.route("/inquiries/<int:inquiry_id>")
@login_required
def inquiry_detail(inquiry_id):
    with get_db() as db:
        inquiry = db.execute("""
            SELECT i.id, i.service_id, i.buyer_id, i.seller_id, i.status,
                   i.created_at, COALESCE(i.seller_deleted,0) as seller_deleted,
                   s.title as service_title, s.image_url as service_image,
                   b.name as buyer_name, b.email as buyer_email, COALESCE(b.is_deleted,0) as buyer_deleted,
                   sl.name as seller_name, sl.email as seller_email
            FROM inquiries i
            LEFT JOIN services s ON i.service_id=s.id
            LEFT JOIN users b ON i.buyer_id=b.id
            LEFT JOIN users sl ON i.seller_id=sl.id
            WHERE i.id=?
        """, (inquiry_id,)).fetchone()
        if not inquiry:
            flash("Inquiry not found.", "danger")
            return redirect(url_for("inquiries"))
        if session["user_id"] not in (inquiry["buyer_id"], inquiry["seller_id"]) and not session.get("is_admin"):
            flash("Access denied.", "danger")
            return redirect(url_for("index"))
        # If seller deleted the conversation, hide it from seller UI.
        if session["user_id"] == inquiry["seller_id"] and int(inquiry["seller_deleted"] or 0):
            flash("This conversation was deleted.", "info")
            return redirect(url_for("inquiries"))

        messages = db.execute("""
            SELECT m.*, u.name as sender_name
            FROM messages m JOIN users u ON m.sender_id=u.id
            WHERE m.inquiry_id=? ORDER BY m.created_at ASC
        """, (inquiry_id,)).fetchall()
        db.execute("UPDATE messages SET is_read=1 WHERE inquiry_id=? AND sender_id != ?", (inquiry_id, session["user_id"]))

        # Seller delete eligibility:
        allow_delete = False
        if session.get("role") == "seller" and session["user_id"] == inquiry["seller_id"]:
            has_order = db.execute("SELECT 1 FROM orders WHERE service_id=? AND buyer_id=? LIMIT 1", (inquiry["service_id"], inquiry["buyer_id"])).fetchone()
            last_msg = db.execute("SELECT created_at FROM messages WHERE inquiry_id=? ORDER BY created_at DESC LIMIT 1", (inquiry_id,)).fetchone()
            last_dt = None
            if last_msg and last_msg["created_at"]:
                try:
                    last_dt = datetime.strptime(last_msg["created_at"], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    last_dt = None
            if inquiry["buyer_deleted"]:
                allow_delete = True
            elif not has_order and last_dt and (datetime.utcnow() - last_dt).days >= 3:
                allow_delete = True

        custom_offers_list = db.execute(
            "SELECT * FROM custom_offers WHERE inquiry_id=? ORDER BY id DESC LIMIT 3",
            (inquiry_id,)
        ).fetchall()
    return render_template("inquiry_detail.html", inquiry=inquiry, messages=messages,
                           allow_delete=allow_delete, custom_offers=custom_offers_list)

@app.route("/inquiries/<int:inquiry_id>/message", methods=["POST"])
@login_required
def inquiry_message(inquiry_id):
    content = request.form.get("message", "").strip()
    if not content:
        return redirect(url_for("inquiry_detail", inquiry_id=inquiry_id))
    with get_db() as db:
        inquiry = db.execute("SELECT * FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
        if not inquiry:
            flash("Inquiry not found.", "danger")
            return redirect(url_for("inquiries"))
        if session["user_id"] not in (inquiry["buyer_id"], inquiry["seller_id"]):
            flash("Access denied.", "danger")
            return redirect(url_for("index"))
        if session["user_id"] == inquiry["seller_id"] and int(inquiry["seller_deleted"] or 0):
            flash("Conversation was deleted.", "info")
            return redirect(url_for("inquiries"))
        db.execute("INSERT INTO messages (inquiry_id, sender_id, content) VALUES (?, ?, ?)", (inquiry_id, session["user_id"], content))
        other_id = inquiry["seller_id"] if session["user_id"] == inquiry["buyer_id"] else inquiry["buyer_id"]
        svc = db.execute("SELECT title FROM services WHERE id=?", (inquiry["service_id"],)).fetchone()
        notify(db, other_id, f"New message from {session['name']}", f"Inquiry about \"{svc['title']}\".", url_for("inquiry_detail", inquiry_id=inquiry_id))
    return redirect(url_for("inquiry_detail", inquiry_id=inquiry_id))

@app.route("/inquiries/<int:inquiry_id>/delete", methods=["POST"])
@login_required
def delete_inquiry(inquiry_id):
    with get_db() as db:
        inquiry = db.execute("""
            SELECT i.*, COALESCE(b.is_deleted,0) as buyer_deleted
            FROM inquiries i JOIN users b ON i.buyer_id=b.id
            WHERE i.id=?
        """, (inquiry_id,)).fetchone()
        if not inquiry:
            flash("Inquiry not found.", "danger")
            return redirect(url_for("inquiries"))
        if session.get("role") != "seller" or session["user_id"] != inquiry["seller_id"]:
            flash("Only the seller can delete this conversation.", "warning")
            return redirect(url_for("inquiry_detail", inquiry_id=inquiry_id))
        has_order = db.execute("SELECT 1 FROM orders WHERE service_id=? AND buyer_id=? LIMIT 1", (inquiry["service_id"], inquiry["buyer_id"])).fetchone()
        last_msg = db.execute("SELECT created_at FROM messages WHERE inquiry_id=? ORDER BY created_at DESC LIMIT 1", (inquiry_id,)).fetchone()
        last_dt = None
        if last_msg and last_msg["created_at"]:
            try:
                last_dt = datetime.strptime(last_msg["created_at"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                last_dt = None
        allowed = False
        if inquiry["buyer_deleted"]:
            allowed = True
        elif not has_order and last_dt and (datetime.utcnow() - last_dt).days >= 3:
            allowed = True
        if not allowed:
            flash("You can only delete after 3 days of inactivity (if no order was placed), or if the buyer deleted their account.", "warning")
            return redirect(url_for("inquiry_detail", inquiry_id=inquiry_id))
        db.execute("UPDATE inquiries SET seller_deleted=1, deleted_at=datetime('now'), status='closed' WHERE id=?", (inquiry_id,))
    flash("Conversation deleted.", "success")
    return redirect(url_for("inquiries"))

@app.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    """Soft-delete account to avoid breaking foreign key relations."""
    uid = session["user_id"]
    with get_db() as db:
        row = db.execute("SELECT id, is_admin FROM users WHERE id=?", (uid,)).fetchone()
        if row and row["is_admin"]:
            flash("Admin accounts cannot be deleted from the UI.", "warning")
            return redirect(url_for("account"))
        deleted_email = f"deleted_{uid}_{int(datetime.utcnow().timestamp())}@deleted.local"
        db.execute("""
            UPDATE users
            SET is_deleted=1,
                deleted_at=datetime('now'),
                is_banned=1,
                name='Deleted User',
                email=?,
                avatar_url=NULL,
                bio=NULL,
                location=NULL,
                website=NULL
            WHERE id=?
        """, (deleted_email, uid))
    session.clear()
    flash("Your account was deleted.", "info")
    return redirect(url_for("index"))

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
                   COALESCE(u.is_available,1) as is_available,
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
        monthly_earnings = db.execute("""
            SELECT strftime('%Y-%m', created_at) as month, COALESCE(SUM(total_price),0) as revenue, COUNT(*) as orders
            FROM orders WHERE seller_id=? AND status='completed'
            GROUP BY month ORDER BY month DESC LIMIT 6
        """, (session["user_id"],)).fetchall()
        monthly_earnings = list(reversed(monthly_earnings))
        seller_level = get_seller_level(
            db.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='completed'", (session["user_id"],)).fetchone()[0],
            db.execute("SELECT COALESCE(AVG(r.rating),0) FROM reviews r JOIN services s ON r.service_id=s.id WHERE s.seller_id=?", (session["user_id"],)).fetchone()[0]
        )
    return render_template("my_services.html", services=services, total_views=total_views,
                           total_earnings=total_earnings, pending_orders=pending_orders, active_orders=active_orders,
                           monthly_earnings=monthly_earnings, seller_level=seller_level)

@app.route("/trending")
def trending():
    with get_db() as db:
        services = db.execute("""
            SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, u.avatar_url as seller_avatar,
                   COALESCE(u.is_available,1) as is_available,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
            FROM services s JOIN categories c ON s.category_id = c.id JOIN users u ON s.seller_id = u.id
            LEFT JOIN reviews r ON r.service_id = s.id
            WHERE s.is_approved=1 GROUP BY s.id ORDER BY s.view_count DESC LIMIT 20
        """).fetchall()
    return render_template("trending.html", services=services)

@app.route("/recommendations")
def recommendations():
    category = request.args.get("category", "")
    uid = session.get("user_id")
    with get_db() as db:
        categories = db.execute("SELECT * FROM categories").fetchall()
        base = """SELECT s.*, c.name as category_name, c.slug as category_slug, u.name as seller_name, u.avatar_url as seller_avatar,
                       COALESCE(u.is_available,1) as is_available,
                       COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count
                FROM services s JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id
                LEFT JOIN reviews r ON r.service_id=s.id WHERE s.is_approved=1"""
        if category:
            services = db.execute(base + " AND c.slug=? GROUP BY s.id ORDER BY s.view_count DESC LIMIT 12", (category,)).fetchall()
        elif uid:
            # Collaborative: find categories the user has ordered/saved, then surface top-rated in those
            user_cats = db.execute("""
                SELECT DISTINCT s.category_id FROM orders o JOIN services s ON o.service_id=s.id WHERE o.buyer_id=?
                UNION
                SELECT DISTINCT s.category_id FROM saved_services sv JOIN services s ON sv.service_id=s.id WHERE sv.user_id=?
            """, (uid, uid)).fetchall()
            cat_ids = [r[0] for r in user_cats]
            if cat_ids:
                placeholders = ",".join("?" * len(cat_ids))
                services = db.execute(
                    base + f" AND s.category_id IN ({placeholders}) AND s.seller_id!=?"
                    " GROUP BY s.id ORDER BY avg_rating DESC, s.view_count DESC LIMIT 12",
                    cat_ids + [uid]
                ).fetchall()
                if not services:
                    services = db.execute(base + " GROUP BY s.id ORDER BY avg_rating DESC, s.view_count DESC LIMIT 12").fetchall()
            else:
                services = db.execute(base + " GROUP BY s.id ORDER BY avg_rating DESC, s.view_count DESC LIMIT 12").fetchall()
        else:
            services = db.execute(base + " GROUP BY s.id ORDER BY avg_rating DESC, s.view_count DESC LIMIT 12").fetchall()
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
            SELECT o.*, s.title as service_title, s.description as service_desc,
                   s.id as svc_id, s.image_url, s.delivery_days,
                   buyer.name as buyer_name, seller.name as seller_name,
                   seller.email as seller_email, buyer.email as buyer_email
            FROM orders o JOIN services s ON o.service_id=s.id
            JOIN users buyer ON o.buyer_id=buyer.id
            JOIN users seller ON o.seller_id=seller.id WHERE o.id=?
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
            elif new_status == "completed" and order["status"] in ("active", "revision_requested"): allowed = True
            elif new_status == "cancelled" and order["status"] == "pending": allowed = True
        if uid == order["buyer_id"]:
            if new_status == "cancelled" and order["status"] == "pending": allowed = True
            elif new_status == "completed" and order["status"] in ("active", "revision_requested"): allowed = True
            elif new_status == "revision_requested" and order["status"] == "active": allowed = True
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
               COALESCE(u.is_available,1) as is_available,
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
    seller_level = get_seller_level(completed_orders, avg_rating)
    return render_template("profile.html", profile_user=user, services=services,
                           completed_orders=completed_orders, avg_rating=avg_rating,
                           review_count=review_count, recent_reviews=recent_reviews,
                           seller_level=seller_level)

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
            elif action == "availability":
                is_available = 1 if request.form.get("is_available") else 0
                available_from = request.form.get("available_from","").strip() or None
                db.execute("UPDATE users SET is_available=?, available_from=? WHERE id=?", (is_available, available_from, session["user_id"]))
                flash("Availability updated!", "success")
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

# ── Service FAQs ────────────────────────────────────────────────────────────
@app.route("/services/<int:service_id>/faqs", methods=["GET", "POST"])
@seller_required
def manage_faqs(service_id):
    with get_db() as db:
        svc = db.execute("SELECT id, title FROM services WHERE id=? AND seller_id=?", (service_id, session["user_id"])).fetchone()
        if not svc:
            flash("Service not found.", "danger")
            return redirect(url_for("my_services"))
        if request.method == "POST":
            db.execute("DELETE FROM service_faqs WHERE service_id=?", (service_id,))
            questions = request.form.getlist("question")
            answers = request.form.getlist("answer")
            for i, (q, a) in enumerate(zip(questions, answers)):
                q, a = q.strip(), a.strip()
                if q and a:
                    db.execute("INSERT INTO service_faqs (service_id, question, answer, sort_order) VALUES (?,?,?,?)", (service_id, q, a, i))
            flash("FAQs saved!", "success")
            return redirect(url_for("service_detail", service_id=service_id))
        faqs = db.execute("SELECT * FROM service_faqs WHERE service_id=? ORDER BY sort_order", (service_id,)).fetchall()
    return render_template("manage_faqs.html", service=svc, faqs=faqs)

# ── Service Packages ─────────────────────────────────────────────────────────
@app.route("/services/<int:service_id>/packages", methods=["POST"])
@seller_required
def save_packages(service_id):
    with get_db() as db:
        svc = db.execute("SELECT id FROM services WHERE id=? AND seller_id=?", (service_id, session["user_id"])).fetchone()
        if not svc:
            flash("Service not found.", "danger")
            return redirect(url_for("my_services"))
        tiers = ["basic", "standard", "premium"]
        pkgs = []
        for tier in tiers:
            title = request.form.get(f"{tier}_title", "").strip()
            price = request.form.get(f"{tier}_price", type=int, default=0)
            delivery = request.form.get(f"{tier}_delivery", type=int, default=3)
            description = request.form.get(f"{tier}_description", "").strip()
            if title and price:
                pkgs.append({"tier": tier, "title": title, "price": price, "delivery_days": delivery, "description": description})
        db.execute("UPDATE services SET packages=? WHERE id=?", (json.dumps(pkgs) if pkgs else None, service_id))
    flash("Packages saved!", "success")
    return redirect(url_for("service_detail", service_id=service_id))

# ── Custom Offers ─────────────────────────────────────────────────────────────
@app.route("/inquiries/<int:inquiry_id>/offer", methods=["POST"])
@login_required
def send_custom_offer(inquiry_id):
    price = request.form.get("price", type=int)
    delivery_days = request.form.get("delivery_days", type=int, default=3)
    description = request.form.get("description", "").strip()
    if not price or price < 1:
        flash("Please enter a valid price.", "danger")
        return redirect(url_for("inquiry_detail", inquiry_id=inquiry_id))
    with get_db() as db:
        inquiry = db.execute("SELECT * FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
        if not inquiry or session["user_id"] != inquiry["seller_id"]:
            flash("Access denied.", "danger")
            return redirect(url_for("inquiries"))
        db.execute("UPDATE custom_offers SET status='superseded' WHERE inquiry_id=? AND status='pending'", (inquiry_id,))
        db.execute("""INSERT INTO custom_offers (inquiry_id, seller_id, buyer_id, service_id, price, delivery_days, description)
                      VALUES (?,?,?,?,?,?,?)""",
                   (inquiry_id, inquiry["seller_id"], inquiry["buyer_id"], inquiry["service_id"], price, delivery_days, description))
        offer_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        svc = db.execute("SELECT title FROM services WHERE id=?", (inquiry["service_id"],)).fetchone()
        notify(db, inquiry["buyer_id"], "Custom Offer Received!",
               f"{session['name']} sent a custom offer for Rs.{price:,} for \"{svc['title'] if svc else 'service'}\".",
               url_for("inquiry_detail", inquiry_id=inquiry_id))
    flash("Custom offer sent!", "success")
    return redirect(url_for("inquiry_detail", inquiry_id=inquiry_id))

@app.route("/custom-offers/<int:offer_id>/accept", methods=["POST"])
@login_required
def accept_custom_offer(offer_id):
    with get_db() as db:
        offer = db.execute("SELECT * FROM custom_offers WHERE id=?", (offer_id,)).fetchone()
        if not offer or offer["buyer_id"] != session["user_id"] or offer["status"] != "pending":
            flash("Offer not found or expired.", "danger")
            return redirect(url_for("inquiries"))
        db.execute("UPDATE custom_offers SET status='accepted' WHERE id=?", (offer_id,))
        payment_ref = f"PAY{random.randint(100000000, 999999999)}"
        db.execute("""INSERT INTO orders (service_id, buyer_id, seller_id, status, payment_method, payment_ref, total_price, notes)
                      VALUES (?,?,?,'pending','custom_offer',?,?,?)""",
                   (offer["service_id"], offer["buyer_id"], offer["seller_id"], payment_ref, offer["price"],
                    offer["description"] or "Custom offer order"))
        order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("UPDATE inquiries SET status='closed' WHERE id=?", (offer["inquiry_id"],))
        svc = db.execute("SELECT title FROM services WHERE id=?", (offer["service_id"],)).fetchone()
        title = svc["title"] if svc else "service"
        notify(db, offer["seller_id"], "Custom Offer Accepted!", f"{session['name']} accepted your offer for \"{title}\".", url_for("order_detail", order_id=order_id))
        notify(db, session["user_id"], "Order Placed!", f"Order for \"{title}\". Ref: {payment_ref}", url_for("order_detail", order_id=order_id))
    flash(f"Offer accepted! Order placed. Ref: {payment_ref}", "success")
    return redirect(url_for("order_detail", order_id=order_id))

@app.route("/custom-offers/<int:offer_id>/decline", methods=["POST"])
@login_required
def decline_custom_offer(offer_id):
    with get_db() as db:
        offer = db.execute("SELECT * FROM custom_offers WHERE id=?", (offer_id,)).fetchone()
        if not offer or offer["buyer_id"] != session["user_id"]:
            flash("Offer not found.", "danger")
            return redirect(url_for("inquiries"))
        db.execute("UPDATE custom_offers SET status='declined' WHERE id=?", (offer_id,))
        notify(db, offer["seller_id"], "Custom Offer Declined", f"{session['name']} declined your custom offer.", url_for("inquiry_detail", inquiry_id=offer["inquiry_id"]))
    flash("Offer declined.", "info")
    return redirect(url_for("inquiry_detail", inquiry_id=offer["inquiry_id"]))

# ── Revision Request ──────────────────────────────────────────────────────────
@app.route("/orders/<int:order_id>/request-revision", methods=["POST"])
@login_required
def request_revision(order_id):
    notes = request.form.get("notes", "").strip()
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order or order["buyer_id"] != session["user_id"] or order["status"] != "active":
            flash("Cannot request revision at this stage.", "warning")
            return redirect(url_for("order_detail", order_id=order_id))
        db.execute("UPDATE orders SET status='revision_requested', revision_notes=?, revision_requested_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
                   (notes, order_id))
        svc = db.execute("SELECT title FROM services WHERE id=?", (order["service_id"],)).fetchone()
        notify(db, order["seller_id"], "Revision Requested",
               f"{session['name']} requested a revision on \"{svc['title'] if svc else 'your service'}\": {notes[:60]}",
               url_for("order_detail", order_id=order_id))
    flash("Revision requested. The seller has been notified.", "info")
    return redirect(url_for("order_detail", order_id=order_id))

# ── Export Orders CSV ─────────────────────────────────────────────────────────
@app.route("/orders/export")
@login_required
def export_orders():
    import csv, io
    with get_db() as db:
        if session.get("role") == "seller":
            rows = db.execute("""SELECT o.id, s.title, o.total_price, o.status, o.payment_method, o.payment_ref, u.name as buyer_name, o.created_at
                FROM orders o JOIN services s ON o.service_id=s.id JOIN users u ON o.buyer_id=u.id
                WHERE o.seller_id=? ORDER BY o.created_at DESC""", (session["user_id"],)).fetchall()
            headers = ["Order ID", "Service", "Amount (Rs.)", "Status", "Payment", "Ref", "Buyer", "Date"]
        else:
            rows = db.execute("""SELECT o.id, s.title, o.total_price, o.status, o.payment_method, o.payment_ref, u.name as seller_name, o.created_at
                FROM orders o JOIN services s ON o.service_id=s.id JOIN users u ON o.seller_id=u.id
                WHERE o.buyer_id=? ORDER BY o.created_at DESC""", (session["user_id"],)).fetchall()
            headers = ["Order ID", "Service", "Amount (Rs.)", "Status", "Payment", "Ref", "Seller", "Date"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for r in rows:
        writer.writerow([r[0], r[1], r[2] / 100 if r[2] else 0, r[3], r[4], r[5], r[6], r[7]])
    from flask import make_response
    resp = make_response(output.getvalue())
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = "attachment; filename=orders.csv"
    return resp

# ── Buyer Request Board ───────────────────────────────────────────────────────
@app.route("/buyer-requests", methods=["GET", "POST"])
@login_required
def buyer_requests():
    with get_db() as db:
        categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
        if request.method == "POST":
            if session.get("role") != "buyer":
                flash("Only buyers can post requests.", "warning")
                return redirect(url_for("buyer_requests"))
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            budget = request.form.get("budget", type=int, default=0)
            category_id = request.form.get("category_id", type=int)
            if not title or len(title) < 5:
                flash("Title must be at least 5 characters.", "danger")
            elif not description or len(description) < 20:
                flash("Description must be at least 20 characters.", "danger")
            else:
                db.execute("INSERT INTO buyer_requests (title, description, budget, category_id, buyer_id) VALUES (?,?,?,?,?)",
                           (title, description, budget or 0, category_id, session["user_id"]))
                flash("Request posted! Sellers will submit proposals.", "success")
                return redirect(url_for("buyer_requests"))
        requests_list = db.execute("""
            SELECT br.*, u.name as buyer_name, c.name as category_name,
                   COUNT(p.id) as proposal_count
            FROM buyer_requests br JOIN users u ON br.buyer_id=u.id
            LEFT JOIN categories c ON br.category_id=c.id
            LEFT JOIN proposals p ON p.request_id=br.id
            WHERE br.status='open' GROUP BY br.id ORDER BY br.created_at DESC LIMIT 30
        """).fetchall()
    return render_template("buyer_requests.html", requests=requests_list, categories=categories)

@app.route("/buyer-requests/<int:req_id>", methods=["GET", "POST"])
@login_required
def buyer_request_detail(req_id):
    with get_db() as db:
        req = db.execute("""SELECT br.*, u.name as buyer_name, c.name as category_name
            FROM buyer_requests br JOIN users u ON br.buyer_id=u.id
            LEFT JOIN categories c ON br.category_id=c.id WHERE br.id=?""", (req_id,)).fetchone()
        if not req:
            flash("Request not found.", "danger")
            return redirect(url_for("buyer_requests"))
        if request.method == "POST":
            if session.get("role") != "seller":
                flash("Only sellers can submit proposals.", "warning")
                return redirect(url_for("buyer_request_detail", req_id=req_id))
            if req["status"] != "open":
                flash("This request is closed.", "warning")
                return redirect(url_for("buyer_request_detail", req_id=req_id))
            existing = db.execute("SELECT id FROM proposals WHERE request_id=? AND seller_id=?", (req_id, session["user_id"])).fetchone()
            if existing:
                flash("You already submitted a proposal.", "warning")
                return redirect(url_for("buyer_request_detail", req_id=req_id))
            msg = request.form.get("message","").strip()
            price = request.form.get("price", type=int)
            delivery = request.form.get("delivery_days", type=int, default=3)
            if not msg or not price:
                flash("Message and price are required.", "danger")
            else:
                db.execute("INSERT INTO proposals (request_id, seller_id, message, price, delivery_days) VALUES (?,?,?,?,?)",
                           (req_id, session["user_id"], msg, price, delivery))
                notify(db, req["buyer_id"], "New Proposal!", f"{session['name']} sent a proposal for your request \"{req['title']}\".",
                       url_for("buyer_request_detail", req_id=req_id))
                flash("Proposal submitted!", "success")
                return redirect(url_for("buyer_request_detail", req_id=req_id))
        proposals_list = db.execute("""SELECT p.*, u.name as seller_name, u.avatar_url as seller_avatar,
            (SELECT COUNT(*) FROM orders WHERE seller_id=p.seller_id AND status='completed') as completed_orders
            FROM proposals p JOIN users u ON p.seller_id=u.id WHERE p.request_id=? ORDER BY p.created_at""", (req_id,)).fetchall()
        already_proposed = bool(db.execute("SELECT id FROM proposals WHERE request_id=? AND seller_id=?", (req_id, session["user_id"])).fetchone()) if session.get("role") == "seller" else False
    return render_template("request_detail.html", req=req, proposals=proposals_list, already_proposed=already_proposed)

@app.route("/buyer-requests/<int:req_id>/proposals/<int:prop_id>/accept", methods=["POST"])
@login_required
def accept_proposal(req_id, prop_id):
    with get_db() as db:
        req = db.execute("SELECT * FROM buyer_requests WHERE id=? AND buyer_id=?", (req_id, session["user_id"])).fetchone()
        if not req:
            flash("Access denied.", "danger")
            return redirect(url_for("buyer_requests"))
        prop = db.execute("SELECT * FROM proposals WHERE id=? AND request_id=?", (prop_id, req_id)).fetchone()
        if not prop:
            flash("Proposal not found.", "danger")
            return redirect(url_for("buyer_request_detail", req_id=req_id))
        db.execute("UPDATE buyer_requests SET status='closed' WHERE id=?", (req_id,))
        db.execute("UPDATE proposals SET status='accepted' WHERE id=?", (prop_id,))
        db.execute("UPDATE proposals SET status='declined' WHERE request_id=? AND id!=?", (req_id, prop_id))
        notify(db, prop["seller_id"], "Proposal Accepted!", f"{session['name']} accepted your proposal for \"{req['title']}\".",
               url_for("buyer_request_detail", req_id=req_id))
    flash("Proposal accepted! Contact the seller to proceed.", "success")
    return redirect(url_for("buyer_request_detail", req_id=req_id))

@app.route("/buyer-requests/<int:req_id>/close", methods=["POST"])
@login_required
def close_buyer_request(req_id):
    with get_db() as db:
        req = db.execute("SELECT * FROM buyer_requests WHERE id=? AND buyer_id=?", (req_id, session["user_id"])).fetchone()
        if req:
            db.execute("UPDATE buyer_requests SET status='closed' WHERE id=?", (req_id,))
            flash("Request closed.", "info")
    return redirect(url_for("buyer_requests"))

# ── Service Comparison API ────────────────────────────────────────────────────
@app.route("/api/compare")
def api_compare():
    ids_raw = request.args.get("ids", "")
    try:
        ids = [int(x) for x in ids_raw.split(",") if x.strip()][:3]
    except ValueError:
        return jsonify([])
    if not ids:
        return jsonify([])
    with get_db() as db:
        placeholders = ",".join("?" * len(ids))
        rows = db.execute(f"""
            SELECT s.id, s.title, s.price, s.delivery_days,
                   COALESCE(AVG(r.rating),0) as avg_rating, COUNT(DISTINCT r.id) as review_count,
                   c.name as category_name, u.name as seller_name,
                   (SELECT COUNT(*) FROM orders WHERE seller_id=s.seller_id AND status='completed') as completed_orders
            FROM services s JOIN categories c ON s.category_id=c.id JOIN users u ON s.seller_id=u.id
            LEFT JOIN reviews r ON r.service_id=s.id
            WHERE s.id IN ({placeholders}) GROUP BY s.id
        """, ids).fetchall()
    return jsonify([dict(r) for r in rows])

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
    app.run(debug=debug, host="0.0.0.0", port=port, threaded=True)
