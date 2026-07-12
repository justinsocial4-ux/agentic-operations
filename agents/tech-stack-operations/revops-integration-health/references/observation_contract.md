# Observation contract

Each pseudonymous integration contract contains exactly five independent lanes:

1. `source-endpoint`: compare one recorded token with the exact customer-authored expected token.
2. `connector-job`: compare one recorded token with the exact customer-authored expected token.
3. `destination-endpoint`: compare one recorded token with the exact customer-authored expected token.
4. `checkpoint`: compute cutoff minus checkpoint in whole seconds and compare it with the customer-authored maximum age.
5. `reconciliation`: compute exact non-negative integer source total minus target total under `source-total-equals-target-total`.

Each lane has its own definition receipt and evidence receipt. A lane match proves only that exact comparison. It does not prove semantic correctness, record identity, field correctness, complete delivery outside the declared measure, health, availability, cause, impact, or fitness for downstream use.
