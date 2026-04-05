# Bounded Context Naming Rules

When helping engineers name bounded contexts, apply these rules:

**The litmus test:** Does this name answer "what does this system do?"
without needing elaboration?

## Four naming smells

1. **Too concrete / physical** — names a place or thing, not a capability.
   `Warehouse` -> what *about* the warehouse? -> `Warehouse Management`

2. **Redundant verb** — adds an activity word to a name that already
   implies activity. `Pricing Computing` -> `Pricing` already means
   computing prices. `Shipping Shipping` -> just `Shipping`.

3. **Too abstract / generic** — so vague it could mean anything.
   `Core Service`, `Platform`, `Engine` -> name the actual capability.

4. **Entity-named** — named after a data entity, not a behavior.
   `Orders`, `Products`, `Users` -> what does the system *do* with them?

## The rule

> A bounded context name should be a **noun or noun phrase that
> inherently implies a capability**. If the noun alone doesn't convey
> what the system does, add a gerund/activity word. If it already does,
> don't.

## Examples

| Subdomain             | BC name          | Why it works                                      |
|-----------------------|------------------|---------------------------------------------------|
| Order Fulfillment     | Order Fulfillment | "Fulfillment" already implies the activity        |
| Product Catalog       | Product Catalog   | Clear what it does — catalogs products            |
| Pricing & Promotions  | Pricing           | "Pricing" already means computing prices          |
| Pricing & Promotions  | Promotion Management | "Promotions" alone is entity-named; needs verb |
| Inventory Management  | Warehouse Management | "Warehouse" alone is a place; needs verb       |
| Payment Processing    | Payment Processing | Activity-oriented, self-explanatory              |

## 1:1 mapping rule

If a bounded context maps 1:1 to a subdomain, **keep the same name**.
Only rename when the BC represents a genuinely different decomposition
from the subdomain.
