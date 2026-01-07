# Bookstore E-commerce System - Software Requirements Specification

## Functional Requirements
- Customer management (CRUD)
- Product catalogue with full-text search
- Vendor management mapped to publishers
- Invoice reporting for recent orders

## Non-functional Requirements
- PostgreSQL backend with pg_trgm and pgcrypto extensions
- Dockerised deployment
- Performance targets: search p95 ≤ 150ms
