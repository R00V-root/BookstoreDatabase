# Requirements Traceability Matrix

| Requirement | Implementation | Tests |
|-------------|----------------|-------|
| Checkout ACID semantics | `Order.checkout_from_cart` uses transactions and `select_for_update` | `tests/store/test_models.py::test_checkout_reserves_inventory` |
| Inventory not oversold | `Inventory.allocate` validation | `tests/store/test_models.py::test_checkout_fails_when_inventory_low` |
