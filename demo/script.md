# Demo Script

1. Start the stack: `docker-compose up --build`.
2. Apply migrations: automatically executed on container start.
3. Load sample data: `python manage.py loaddata demo/sample.json` (placeholder).
4. Navigate to `http://localhost:8000/store/login/` and sign in with admin credentials.
5. Use the hub to create a customer, add products, associate with a vendor, and create an invoice.
6. View the report tab to see invoices from the last 7 days.
