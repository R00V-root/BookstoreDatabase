-- Placeholder EXPLAIN plan for allocating inventory during checkout.
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM inventory WHERE book_id = 1 FOR UPDATE;
