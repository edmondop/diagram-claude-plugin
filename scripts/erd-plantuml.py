# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Entity-Relationship Diagram using PlantUML's native entity syntax.

PlantUML produces cleaner ERDs than graphviz: dedicated entity shapes,
PK/FK separators, crow's foot notation, and annotation notes — all with
minimal markup.

Uses the public PlantUML server (no Java required locally).

Run: uv run erd-plantuml.py
"""

import zlib
from pathlib import Path
from urllib.request import Request, urlopen

DIAGRAM = """\
@startuml
skinparam backgroundColor white
skinparam class {
  BackgroundColor #FAFAFA
  BorderColor #555555
  FontColor #222222
  FontSize 12
  BorderThickness 1.5
}
skinparam note {
  BackgroundColor #FFFDE7
  BorderColor #FBC02D
}

hide methods
hide stereotypes

title E-Commerce ERD

entity "User" as user {
  * id : UUID <<PK>>
  --
  * email : VARCHAR
  * name : VARCHAR
  * created_at : TIMESTAMP
}

entity "Order" as order {
  * id : UUID <<PK>>
  --
  * user_id : UUID <<FK>>
  * status : ENUM
  * total_cents : INTEGER
  * placed_at : TIMESTAMP
}

entity "OrderItem" as order_item {
  * id : UUID <<PK>>
  --
  * order_id : UUID <<FK>>
  * product_id : UUID <<FK>>
  * quantity : INTEGER
  * unit_price_cents : INTEGER
}

entity "Product" as product {
  * id : UUID <<PK>>
  --
  * category_id : UUID <<FK>>
  * name : VARCHAR
  * price_cents : INTEGER
}

entity "Category" as category {
  * id : UUID <<PK>>
  --
  * parent_id : UUID <<FK>> (nullable)
  * name : VARCHAR
  * slug : VARCHAR
}

user ||--o{ order : "places"
order ||--o{ order_item : "contains"
product ||--o{ order_item : "referenced by"
category ||--o{ product : "classifies"
category ||--o| category : "parent"

note right of order_item
  Junction table linking
  orders to products with
  quantity and price snapshot
end note
@enduml
"""


def _plantuml_encode(text: str) -> str:
    """Encode PlantUML text for the HTTP server URL."""
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    result = []
    for i in range(0, len(compressed), 3):
        chunk = compressed[i : i + 3]
        b0 = chunk[0]
        b1 = chunk[1] if len(chunk) > 1 else 0
        b2 = chunk[2] if len(chunk) > 2 else 0
        result.append(alphabet[b0 >> 2])
        result.append(alphabet[((b0 & 0x3) << 4) | (b1 >> 4)])
        result.append(alphabet[((b1 & 0xF) << 2) | (b2 >> 6)])
        result.append(alphabet[b2 & 0x3F])
    return "".join(result)


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    encoded = _plantuml_encode(DIAGRAM)
    url = f"https://www.plantuml.com/plantuml/svg/{encoded}"

    req = Request(url, headers={"User-Agent": "diagram-plugin/1.0"})
    with urlopen(req) as resp:
        svg = resp.read()

    out = Path("output/erd-plantuml.svg")
    out.write_bytes(svg)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
