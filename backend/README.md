# HUTKO — Backend API

Flask backend for hutko.nl — handles auth, orders, contact form and Excel export.

## Project structure
```
backend/
  app.py            ← Flask entry point
  database.py       ← SQLite setup, all table definitions
  auth.py           ← /api/register /api/login /api/logout /api/me /api/profile /api/address
  orders.py         ← /api/checkout /api/orders
  contact.py        ← /api/contact /api/newsletter
  admin.py          ← /api/admin/export /api/admin/stats /api/admin/login
  requirements.txt  ← Python dependencies
  render.yaml       ← Render deployment config
  .env.example      ← Environment variable template
  api.js            ← Frontend JS client (copy to frontend/js/)
```

## Run locally

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit .env with your values
python app.py
```
API will be running at `http://localhost:5000`
Test with: `curl http://localhost:5000/api/health`

## Deploy to Render

1. Push this repo to GitHub (backend folder must exist)
2. Go to render.com → New Web Service → connect repo
3. Set:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
4. Add environment variables in Render dashboard:
   - `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ADMIN_PASSWORD` — choose a strong password
   - `RESEND_API_KEY` — from resend.com (free: 3000 emails/month)
   - `FRONTEND_URL` — https://hutko.netlify.app

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET  | /api/health | Health check |
| POST | /api/register | Create account |
| POST | /api/login | Sign in |
| POST | /api/logout | Sign out |
| GET  | /api/me | Get current user |
| PUT  | /api/profile | Update name/phone/password |
| PUT  | /api/address | Save delivery address |
| POST | /api/checkout | Place order |
| GET  | /api/orders | Get my orders |
| GET  | /api/orders/:ref | Get single order |
| POST | /api/contact | Contact form |
| POST | /api/newsletter | Newsletter signup |
| POST | /api/admin/login | Admin login |
| GET  | /api/admin/stats | Dashboard stats |
| GET  | /api/admin/export | Download Excel (admin only) |

## Excel export

Visit `/api/admin/export` in browser (after admin login) to download a fresh `.xlsx` with 4 sheets:
- **Orders** — all orders with items, address, total, status
- **Users** — registered accounts
- **Messages** — contact form submissions
- **Newsletter** — email subscribers

## Wire frontend to backend

1. Copy `api.js` to `frontend/js/api.js`
2. Add `<script src="js/api.js"></script>` to all HTML pages (before `components.js`)
3. Replace `localStorage`-based auth calls with `Api.Auth.login()`, `Api.Auth.register()` etc.
4. Replace checkout form submit with `Api.Orders.checkout(payload)`
5. Replace contact form submit with `Api.Contact.send(...)`
