# Matching Policy

Use exact approved stable IDs for stage, competitor, vertical, objection, product, segment, and deal type. A playbook declares only the criteria it requires; every declared criterion must match. Missing required context returns `CONTEXT_REQUIRED`.

Select the unique lowest approved integer priority among valid matches. A tied best priority returns `AMBIGUOUS_MATCH`. Optional semantic reranking requires a named model/version, approved content/privacy scope, labeled evaluation set, predeclared threshold, and measured validation. Similarity is not confidence or causal relevance.
