# Taxonomy And Methodology Controls

## Approved configuration

Require a taxonomy/rubric ID, version, owner, effective date, allowed categories, inclusion/exclusion examples, tie/conflict rule, reviewer role, and downstream-use limits. Do not fall back to a universal objection list, competitor list, MEDDICC/SPICED definition, severity scale, or score.

## Safe tags

A tag connects an exact statement to an approved category. Examples:

- `budget_constraint`
- `named_alternative`
- `stated_action`
- `stated_date_text`
- `methodology_element_evidence`

The customer may use different IDs. Do not rename or merge them silently.

## Unsafe expansions

Do not derive:

- severity, urgency, deal impact, buying intent, objection resolution, or response effectiveness;
- likelihood that a named product is a live competitor;
- authority or economic-buyer status from title or phrasing;
- methodology adherence percentage, discovery quality, or “gap” score;
- coaching priority, employee quality, or risk.

## Methodology review

For each approved element, return:

- `EVIDENCE_PRESENT` with exact quote(s);
- `NO_EVIDENCE_LOCATED` within the reviewed scope; or
- `NOT_REVIEWED`.

Do not equate one mention with mastery. Do not call missing transcript evidence a rep failure. If the rubric requires order, repetition, depth, or a specific actor, apply only the exact approved rule and show the receipt.

## Commitments and dates

Record action, stated actor, exact date phrase, and locator. If the actor is unstated, return `ACTOR_UNSTATED`. If the date is relative, return `DATE_ANCHOR_REQUIRED` unless an approved call-time/timezone rule exists. A statement is not proof the action was completed.
