# MediStock

A Django inventory management system for clinical and pharmacy stock control. Staff can manage medicines, suppliers, stock batches, and stock movements from a protected dashboard, while tracking low stock items, expiring batches, and recent inventory activity.

## Screenshots

<div align="left">
  <p float="left">
    <img src="static/images/screenshot1.png" width="45%" />
    <img src="static/images/screenshot2.png" width="45%" />
  </p>
</div>

## Features

- Login-protected inventory workspace
- Dashboard with inventory metrics
- Low stock batch alerts
- Expiring batch alerts for the next 30 days
- Recent stock movement overview
- Medicine catalog management
- Medicine search by name, generic name, and category
- Supplier management
- Stock batch management with expiry dates
- Stock in and stock out movement tracking
- Automatic batch quantity updates when movements are created, edited, or deleted
- Insufficient stock validation for stock out movements
- Atomic stock movement workflow to keep quantities consistent
- Django admin management for suppliers, medicines, batches, and movements
- Demo data seeding command with optional demo user
- Responsive custom dashboard UI

## Tech Stack

- Python
- Django
- PostgreSQL
- python-decouple
- HTML/CSS

## Main Pages

- `/accounts/login/` - Staff login
- `/` - Inventory dashboard
- `/medicines/` - Medicine catalog and search
- `/medicines/add/` - Add medicine
- `/suppliers/` - Supplier management
- `/batches/` - Stock batch management
- `/movements/` - Stock movement history
- `/movements/add/` - Record stock in or stock out
- `/admin/` - Django admin

## Setup Instructions

```bash
git clone https://github.com/vfb-dev/medistock.git
cd medistock

python -m venv env
env\Scripts\activate

pip install -r requirements.txt
```

Create a PostgreSQL database, then add a `.env` file in the project root:

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
DB_NAME=medistock
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
```

Run the database setup and start the development server:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data --reset-demo
python manage.py runserver
```

The demo seed command also creates a demo login by default:

```text
Username: demo
Password: demo12345
```

## Author

vfb-dev - Turning ideas into web apps
