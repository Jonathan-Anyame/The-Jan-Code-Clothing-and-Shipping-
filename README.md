# The Jan Code

Flask site for The Jan Code — product sourcing from China and worldwide shipping.

## Screenshots

![Home](docs/screenshots/home.png)
![Sourcing](docs/screenshots/sourcing.png)
![Shipping](docs/screenshots/shipping.png)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Open http://127.0.0.1:5000

## Pages

- `/` — home
- `/buy-from-china` — sourcing info
- `/shipping` — shipping rates
- `/contact` — contact form + WhatsApp/email

## Files

- `server.py` — Flask routes
- `templates/` — HTML
- `static/` — CSS, JS, images

## Author

Jonathan-Anyame — https://github.com/Jonathan-Anyame
