# FreelanceHub 🚀
**India's Premium Freelance Marketplace** — Built with Flask · SQLite · Vanilla JS

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎨 Premium UI | Dark luxury design with Syne + DM Sans fonts |
| 🤖 AI Chatbot | Smart assistant that finds services & answers questions |
| 💬 Pre-Purchase Chat | Message sellers before paying |
| 🔒 Private Order Chat | Secure on-platform communication after ordering |
| 📸 Auto Service Images | Relevant Unsplash images auto-assigned per service |
| 💰 AI Price Suggestions | Market-based pricing recommendations |
| 🏷️ Smart Categorisation | AI auto-detects service category |
| ⭐ Verified Reviews | Only completed-order buyers can review |
| 🔔 Notifications | Real-time platform notifications |
| 🛡️ Admin Panel | Full user/service/order/ticket management |
| 🎫 Help & Support | FAQ + ticket system with admin replies |
| ❤️ Wishlists | Save services for later |
| 📊 Seller Dashboard | Earnings, views, order stats |

---

## 🏃 Running Locally (Step-by-Step from VS Code)

### 1. Install Python
Download Python 3.10+ from https://python.org/downloads and install it.
Make sure to tick **"Add Python to PATH"** during installation.

### 2. Open in VS Code
```
File → Open Folder → select the FreelanceHub folder
```

### 3. Open Terminal in VS Code
```
Terminal → New Terminal  (or Ctrl + `)
```

### 4. Create Virtual Environment
```bash
python -m venv venv
```

### 5. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac/Linux:**
```bash
source venv/bin/activate
```
You'll see `(venv)` appear in the terminal prompt.

### 6. Install Dependencies
```bash
pip install -r freelancehub/requirements.txt
```

### 7. Run the App
```bash
python run.py
```

### 8. Open in Browser
Visit: **http://127.0.0.1:5000**

The database is created automatically on first run with demo data.

### Demo Accounts
| Role | Email | Password |
|---|---|---|
| Buyer | carol@demo.com | password123 |
| Seller | alice@demo.com | password123 |
| Seller | bob@demo.com | password123 |
| Admin | admin@freelancehub.com | admin123 |

---

## 🌐 Deploying to Render (Live Hosting)

### Step 1 — Push to GitHub

1. Create a free account at https://github.com
2. Create a new repository (e.g. `freelancehub`)
3. In VS Code terminal (with venv active):
```bash
git init
git add .
git commit -m "Initial FreelanceHub deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/freelancehub.git
git push -u origin main
```
(Replace `YOUR_USERNAME` with your GitHub username)

### Step 2 — Deploy on Render

1. Go to https://render.com and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select your repository
4. Fill in the settings:

| Setting | Value |
|---|---|
| **Name** | freelancehub |
| **Environment** | Python 3 |
| **Build Command** | `pip install -r freelancehub/requirements.txt` |
| **Start Command** | `gunicorn --chdir freelancehub app:app --workers 2 --threads 2 --bind 0.0.0.0:$PORT --timeout 120` |
| **Instance Type** | Free |

5. Under **Environment Variables**, add:
   - `SECRET_KEY` → click **"Generate"** for a random secure key
   - `FLASK_DEBUG` → `false`

6. Under **Disks** (optional, for persistent uploads):
   - Name: `uploads`
   - Mount Path: `/opt/render/project/src/freelancehub/static/uploads`
   - Size: 1 GB

7. Click **"Create Web Service"**

Render will build and deploy automatically. Your live URL will be:
`https://freelancehub.onrender.com`

> **Note:** On the free tier, the app sleeps after 15 min of inactivity and takes ~30s to wake on first request. Upgrade to a paid tier for always-on hosting.

### Step 3 — Future Updates

Every time you push to GitHub, Render auto-deploys:
```bash
git add .
git commit -m "Your changes"
git push
```

---

## 🗂️ Project Structure

```
FreelanceHub/
├── run.py                          # Local dev launcher
├── Procfile                        # Render/Heroku process file
├── render.yaml                     # Render deployment config
├── .gitignore
├── freelancehub/
│   ├── app.py                      # Flask app, all routes & logic
│   ├── requirements.txt
│   ├── freelancehub.db             # Auto-created SQLite database
│   ├── static/
│   │   ├── css/style.css           # Premium design system
│   │   ├── js/main.js              # Interactive features
│   │   └── uploads/                # Uploaded service images
│   └── templates/
│       ├── base.html               # Layout, navbar, footer, chatbot
│       ├── index.html              # Homepage
│       ├── browse.html             # Service browse + filters
│       ├── service_detail.html     # Service page + inquiry chat
│       ├── checkout.html           # Payment selection
│       ├── order_detail.html       # Order + private chat
│       ├── orders.html             # Orders list
│       ├── my_services.html        # Seller dashboard
│       ├── post_service.html       # Create service (AI-powered)
│       ├── edit_service.html       # Edit service
│       ├── profile.html            # Public seller profile
│       ├── account.html            # Account settings
│       ├── notifications.html      # Notification centre
│       ├── help.html               # Help centre + FAQ
│       ├── support.html            # Contact support
│       ├── admin.html              # Admin panel
│       ├── saved.html              # Saved/wishlist
│       ├── trending.html           # Trending services
│       ├── recommendations.html    # For-you page
│       ├── login.html
│       ├── signup.html
│       └── partials/
│           └── service_card.html   # Reusable service card
```

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask 3
- **Database:** SQLite (WAL mode, foreign keys)
- **Auth:** Werkzeug password hashing, Flask sessions
- **Frontend:** Vanilla HTML/CSS/JS (no React, no jQuery)
- **Fonts:** Google Fonts — Syne (display) + DM Sans (body)
- **Icons:** Bootstrap Icons CDN
- **Images:** Unsplash (auto-selected based on service keywords)
- **Deployment:** Gunicorn + Render

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | dev key (change in production!) |
| `PORT` | Port to listen on | 5000 |
| `FLASK_DEBUG` | Enable debug mode | false |

---

*Built with ❤️ in India 🇮🇳*
