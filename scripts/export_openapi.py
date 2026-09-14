from __future__ import annotations

import json
from pathlib import Path

from hirein_api.main import app

OUTPUT = Path(__file__).resolve().parents[1] / "packages" / "generated-client" / "openapi.json"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI exported to {OUTPUT}")


if __name__ == "__main__":
    main()
