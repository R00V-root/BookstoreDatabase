# Architecture Design Record

- **Backend**: Django 4.2 with PostgreSQL 15.
- **Deployment**: Docker Compose orchestrates `web` and `db` services. Web service applies migrations on startup.
- **Database**: Normalised relational schema with associative tables for authors/books and categories/books. Uses order_status enum for lifecycle.
- **Security**: Roles `app_reader`, `app_writer`, `app_admin` provisioned via SQL scripts.
- **Data Generation**: Faker-driven script produces tiered CSV datasets.
