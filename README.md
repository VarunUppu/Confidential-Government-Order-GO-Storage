# Confidential Government Order (GO) Storage

> A secure, web-based platform for managing and distributing confidential government orders across multiple administrative tiers — built with Flask, TinyDB, and AES-256 encryption.

---

## Abstract

The Government Order Storage System (GO Storage System) is a secure, web-based platform designed to streamline the management and distribution of confidential government orders and documents across multiple administrative tiers. Built using Flask and TinyDB, the system facilitates structured communication and data exchange between three distinct roles — Government Officials, Data Collectors, and Local Bodies — each operating within a strictly enforced, role-based access control framework. All sensitive files transmitted through the platform are protected using AES-256 encryption, ensuring that documents remain confidential during both storage and transfer. Additional security layers include Cloudflare Turnstile human verification on the authentication interface, preventing automated access attempts.

---

## Features

- 🔐 **AES-256 Encryption** — all uploaded files are encrypted at rest and during transfer
- 👥 **Role-Based Access Control** — three distinct roles with isolated permissions and dashboards
- 📜 **Order Management** — government officials can issue, track, and manage orders to collectors and local bodies
- 📁 **Encrypted File Sharing** — secure file upload, encryption, and download with decrypt-on-demand
- 📊 **Dynamic Dashboards** — live statistics per role pulled directly from the database
- 🔔 **Real-Time Notifications** — instant alerts for orders, shared documents, and reports with mark-as-read support
- 📝 **Report Submission** — local bodies can submit reports; government and collectors can view them
- 🤖 **Cloudflare Turnstile** — human verification on the login page to prevent automated access
- 🌙 **Dark Mode** — full light/dark theme toggle persisted across sessions via localStorage
- 📱 **Responsive Design** — clean, accessible UI built with custom CSS and the Figtree font

---

## Roles

| Role | Capabilities |
|------|-------------|
| **Government** | Issue orders, manage users, share confidential data, view reports & analytics, receive notifications |
| **Data Collector** | View assigned orders, upload & encrypt files, share data, view reports, receive notifications |
| **Local Body** | View assigned orders, access encrypted files, submit reports, share data, receive notifications |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | TinyDB (JSON-based) |
| Encryption | AES-256 (PyCryptodome) |
| Frontend | Jinja2, Custom CSS, Vanilla JS |
| Security | Cloudflare Turnstile |
| Font | Figtree (Google Fonts) |

---

## Project Structure

```
GO_Storage_System_Redesigned/
├── app.py                        # All routes, auth, encryption logic
├── run3120.bat                   # Windows run script (port 5000)
├── data/
│   └── database.json             # TinyDB database
├── static/
│   ├── css/
│   │   └── style.css             # Full Design B stylesheet + dark mode
│   └── js/
│       └── theme.js              # Theme toggle, active links, alert dismiss
├── templates/
│   ├── base.html                 # Base layout with navbar and sidebar
│   ├── index.html                # Landing page
│   ├── login.html                # Login + Cloudflare Turnstile
│   ├── signup.html               # Registration with role selection
│   ├── government/
│   │   ├── dashboard.html
│   │   ├── issue_order.html
│   │   ├── manage_users.html
│   │   ├── share_data.html
│   │   ├── view_reports.html
│   │   └── notifications.html
│   ├── collector/
│   │   ├── dashboard.html
│   │   ├── upload_file.html
│   │   ├── view_orders.html
│   │   ├── view_reports.html
│   │   ├── share_data.html
│   │   └── notifications.html
│   └── localbody/
│       ├── dashboard.html
│       ├── view_orders.html
│       ├── view_files.html
│       ├── upload_report.html
│       ├── share_data.html
│       └── notifications.html
└── uploads/
    ├── encrypted/                # AES-256 encrypted file storage
    └── decrypted/                # Temporarily decrypted files
```

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/VarunUppu/Confidential-Government-Order-GO-Storage.git
cd Confidential-Government-Order-GO-Storage
```

### 2. Install dependencies

```bash
pip install flask tinydb pycryptodome requests
```

### 3. Configure Cloudflare Turnstile

In `app.py`, replace the placeholder keys with your own from the [Cloudflare Turnstile dashboard](https://dash.cloudflare.com):

```python
TURNSTILE_SECRET_KEY = "your_secret_key_here"
```

In `templates/login.html`, replace the site key:

```html
data-sitekey="your_site_key_here"
```

> For local development, use Cloudflare's test keys:
> - Site key: `1x00000000000000000000AA`
> - Secret key: `1x0000000000000000000000000000000AA`

### 4. Run the application

**Windows:**
```bash
run3120.bat
```

**Or directly:**
```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`

---

## Screenshots

> _Add screenshots of the login page, government dashboard, and dark mode here._

---

## Keywords

`Government Order Management` · `AES-256 Encryption` · `Role-Based Access Control` · `Secure Document Storage` · `Flask Web Application` · `Multi-Tier Administration` · `Cloudflare Turnstile` · `Encrypted File Sharing` · `Real-Time Notifications` · `E-Governance Security`

---

## License

This project is intended for academic and demonstration purposes.

---

> Built with Flask · Secured with AES-256 · Verified by Cloudflare Turnstile
