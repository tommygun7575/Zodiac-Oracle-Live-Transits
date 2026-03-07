def merge_vectors(primary, fallback):

    merged = []

    for i in range(len(primary)):

        p = primary[i]
        f = fallback[i]

        merged.append({
            "lon": p.get("lon") if p.get("lon") is not None else f.get("lon"),
            "lat": p.get("lat") if p.get("lat") is not None else f.get("lat")
        })

    return merged
