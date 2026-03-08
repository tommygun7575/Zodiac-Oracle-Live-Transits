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

            # Horizons observer format:
            # Date ... Lon Lat ...
            if len(parts) >= 5:
                rows.append({
                    "date": parts[0],
                    "longitude_deg": parts[3]
                })

    return rows
