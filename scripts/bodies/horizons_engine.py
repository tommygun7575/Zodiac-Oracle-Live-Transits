from .horizons_client import fetch_ephemeris


def parse_ephemeris(text: str):
    rows = []
    reading = False

    for line in text.splitlines():
        line = line.strip()

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if reading and line:
            parts = line.split()

            if len(parts) >= 4:
                rows.append({
                    "date": parts[0],
                    "longitude_deg": parts[3]
                })

    return rows


def get_body_week(body_id: str, name: str, start: str, stop: str):
    raw = fetch_ephemeris(body_id, start, stop)
    parsed = parse_ephemeris(raw)

    if not parsed:
        raise RuntimeError(f"No parsed data for {name}")

    return name, parsed
