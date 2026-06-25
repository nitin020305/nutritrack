# NutriTrack

Full-stack nutrition tracking app with Flask REST API, JWT auth, email verification, admin panel.

## Folder Structure

```
nutritrack_v2/
├── backend/               ← Flask REST API
│   ├── app/
│   │   ├── models/        ← SQLAlchemy models (User, FoodLog, NutrientCache)
│   │   ├── routes/        ← Blueprints (auth, user, food, analytics, admin)
│   │   ├── services/      ← Business logic (food_parser, usda_api, prediction, mail)
│   │   └── utils/         ← Helpers (auth_helpers, unit_converter, chart_generator)
│   ├── config.py          ← All config (reads from infra/.env)
│   ├── run.py             ← Entry point
│   └── requirements.txt
│
├── frontend/              ← HTML/CSS/JS single-page app
│   ├── templates/index.html
│   └── static/
│       ├── css/main.css
│       └── js/main.js
│
├── database/
│   ├── schema.sql         ← Reference SQL schema
│   └── seed.py            ← Creates admin + demo user
│
└── infra/
    ├── .env               ← Your secrets (never commit this)
    ├── .env.example       ← Template to copy
    ├── .gitignore
    └── docker-compose.yml
```

## Quick Start

```bash
# 1. Install dependencies (Anaconda Prompt)
cd nutritrack_v2/backend
pip install -r requirements.txt
conda install matplotlib -y

# 2. Configure environment
Make an .env file with below details 
# Edit infra/.env with your MAIL_USERNAME, MAIL_PASSWORD , usda apikey etc.


# 3. Run
python run.py
```

Open http://127.0.0.1:5000


## API Endpoints

### Auth
| Method | URL | Description |
|---|---|---|
| POST | /api/auth/register | Sign up |
| POST | /api/auth/login | Login |
| GET | /api/auth/verify-email/<token> | Verify email |
| POST | /api/auth/resend-verification | Resend verify email |
| POST | /api/auth/forgot-password | Send reset link |
| POST | /api/auth/reset-password | Reset password |
| POST | /api/auth/change-password | Change password (JWT) |
| GET | /api/auth/me | Get current user (JWT) |
| POST | /api/auth/refresh | Refresh token |
| DELETE | /api/auth/delete-account | Delete account (JWT) |

### User (JWT required)
| Method | URL | Description |
|---|---|---|
| PUT | /api/user/profile | Complete profile (first time) |
| GET | /api/user/profile | Get profile |
| PUT | /api/user/profile/update | Update profile |
| GET | /api/user/prediction | Weight prediction |

### Food (JWT + email verified)
| Method | URL | Description |
|---|---|---|
| POST | /api/food/log | Log food |
| GET | /api/food/log?date=YYYY-MM-DD | Get logs |
| DELETE | /api/food/log/<id> | Delete log |
| GET | /api/food/search?q=banana | Nutrient lookup |

### Analytics (JWT + email verified)
| Method | URL | Description |
|---|---|---|
| GET | /api/analytics/daily?date= | Daily summary + charts |
| GET | /api/analytics/weekly | 7-day breakdown |
| GET | /api/analytics/monthly | 30-day summary |

### Admin (JWT + admin role)
| Method | URL | Description |
|---|---|---|
| POST | /api/admin/bootstrap | Make first admin |
| GET | /api/admin/stats | Platform stats |
| GET | /api/admin/users | List users (paginated) |
| GET | /api/admin/users/<id> | Get user details |
| PUT | /api/admin/users/<id> | Update role/active/verified |
| DELETE | /api/admin/users/<id> | Delete user |
| GET | /api/admin/logs | All food logs |



## Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password
4. Set in infra/.env:
   ```
   MAIL_USERNAME=your@gmail.com
   MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```


