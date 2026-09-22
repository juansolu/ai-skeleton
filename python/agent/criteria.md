A run is APPROVED only when all of these hold:

1. The answer addresses the task that was asked, not a nearby one.
2. `list_merchants` was called at least once before any recommendation was made.
3. `get_merchant_products` was called for at least one merchant before recommending.
4. The recommended product appears in the tool results — not invented.
5. The recommendation avoids any product the user said they already bought.
6. No tool error was silently ignored.
7. The answer ends with Merchant, Product, Price/interval, and Reason. Under 150 words total.

Score 1-5. Below 4 is REJECTED. Feedback must say what to change, not only what was wrong.
