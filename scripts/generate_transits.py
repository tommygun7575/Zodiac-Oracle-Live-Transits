def generate_feeds():
    dt_now = datetime.datetime.utcnow().replace(microsecond=0)
    ISO_now = dt_now.isoformat() + "Z"

    # -- feed_now.json --
    now_transits, engines = compute_transits(ISO_now)
    feed_now = {
        "datetime_utc": ISO_now,
        "transits": now_transits,
        "metadata": make_metadata(engines),
        "generated_at": now_utc()   # <--- Added here!
    }
    write_feed(feed_now, "docs/feed_now.json")
    print("Generated docs/feed_now.json")

    # -- feed_daily.json --
    daily = []
    for i in range(7):
        dt = dt_now + datetime.timedelta(days=i)
        iso_dt = dt.isoformat() + "Z"
        trn, engines = compute_transits(iso_dt)
        daily.append({
            "datetime_utc": iso_dt,
            "transits": trn
        })
    feed_daily = {
        "days": daily,
        "metadata": make_metadata(engines),
        "generated_at": now_utc()   # <--- Added here!
    }
    write_feed(feed_daily, "docs/feed_daily.json")
    print("Generated docs/feed_daily.json")

    # -- feed_week.json --
    week = []
    for i in range(7):
        dt = dt_now + datetime.timedelta(days=i)
        iso_dt = dt.isoformat() + "Z"
        trn, engines = compute_transits(iso_dt)
        week.append({
            "date": iso_dt[:10],
            "transits": trn
        })
    feed_week = {
        "week": week,
        "metadata": make_metadata(engines),
        "generated_at": now_utc()   # <--- Added here!
    }
    write_feed(feed_week, "docs/feed_week.json")
    print("Generated docs/feed_week.json")

    # -- feed_weekly.json --
    mon = dt_now - datetime.timedelta(days=dt_now.weekday())
    week_dates = [mon + datetime.timedelta(days=i) for i in range(7)]
    weekly = []
    for dt in week_dates:
        iso_dt = dt.isoformat() + "Z"
        trn, engines = compute_transits(iso_dt)
        weekly.append({
            "date": iso_dt[:10],
            "transits": trn
        })
    feed_weekly = {
        "week": weekly,
        "metadata": make_metadata(engines),
        "generated_at": now_utc()   # <--- Added here!
    }
    write_feed(feed_weekly, "docs/feed_weekly.json")
    print("Generated docs/feed_weekly.json")
