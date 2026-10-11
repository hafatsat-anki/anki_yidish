stats_query = """
 SELECT
 SUM(CASE WHEN queue = 0 THEN 1 ELSE 0 END) AS new,
 SUM(CASE WHEN queue = 1 THEN 1 ELSE 0 END) AS learn,
 SUM(CASE WHEN queue = 2 THEN 1 ELSE 0 END) AS review,
 SUM(CASE WHEN queue IN (-2, -3) THEN 1 ELSE 0 END) AS buried,
 SUM(CASE WHEN queue = -1 THEN 1 ELSE 0 END) AS suspended,
 SUM(CASE WHEN type IN (2, 3) AND ivl < 21 AND NOT queue IN (-1, -2, -3) THEN 1 ELSE 0 END) AS young,
 SUM(CASE WHEN type IN (2, 3) AND ivl >= 21 AND NOT queue IN (-1, -2, -3) THEN 1 ELSE 0 END) AS mature,
 --פאר היינט
 -- #128 — due ציילט נאר review/day-learning review; learning בלייבט אין דער קאטאגאריע learn און ווערט נישט געציילט צוויי מאל.
 SUM(CASE WHEN queue IN (2, 3) AND due = {days_from_crt} THEN 1
 ELSE 0
 END) AS due,
 --פארשפעטיגט
 SUM(CASE
 WHEN ((queue IN (2, 3) AND due <= {days_from_crt})
 OR (queue IN (1, 4) AND due <= {current_epoch_1200}))
 AND NOT ((queue IN (2, 3) AND due = {days_from_crt})
 OR (queue IN (1, 4) AND ((due - {next_anki_day_start}) / 86400) = 0))
 THEN 1
 ELSE 0
 END) AS overdue,
 --היינט צוגעלייגט
 SUM(CASE WHEN id > {start_of_anki_epoche_day}000 THEN 1 ELSE 0 END) AS added,
 -- בוגר פאר מארגן (Mature Tomorrow)
 SUM(CASE
 WHEN queue IN (2, 3) AND due = {tommorow_days_from_crt} AND ivl >= 21 THEN 1
 ELSE 0
 END) AS tomorrow_mature,
 -- סך הכל פאר מארגן (Total Tomorrow)
 SUM(CASE
 WHEN queue IN (2, 3) AND due = {tommorow_days_from_crt} THEN 1
 ELSE 0
 END) AS tomorrow_total
FROM cards;
"""

# שאילתה חדשה לסטטיסטיקות זמן וחזרות אמיתיות
# odid != 0 כשכרטיס נמצא בחפיסה מסוננת — ייחוס החזרות לחפיסה המקורית
time_and_reps_query = """
SELECT
 CASE WHEN c.odid != 0 THEN c.odid ELSE c.did END AS deck_id,
 count(r.id) as reps,
 sum(r.time) as time_ms
FROM revlog r
JOIN cards c ON r.cid = c.id
WHERE r.id >= {start_of_anki_epoche_day}000
GROUP BY deck_id
"""

decks_stats_query ="""
SELECT
 c.did AS deck_id,
 -- overdue
 SUM(CASE
 WHEN (((c.queue in (2,3) and c.due <= {days_from_crt}) or (c.queue in (1,4) and c.due <= {current_epoch_1200})) and not ((c.queue in (2,3) and
 (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt}) or (c.queue in (1,4) and
 (((case when c.odue != 0 then c.odue else c.due end) - {next_anki_day_start}) / 86400) = 0)))
 THEN 1
 ELSE 0
 END) AS overdue_count,

 -- total cards
 SUM(CASE
 WHEN (c.did IS NOT NULL) OR (c.odid != 0 AND c.odid IS NOT NULL)
 THEN 1
 ELSE 0
 END) AS total_cards_count,

 -- tomorrow
 SUM(((c.queue in (2,3) and
 (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt_1}) or (c.queue in (1,4) and
 (((case when c.odue != 0 then c.odue else c.due end) - {next_anki_day_start_86400}) / 86400) = 0)))
 AS tomorrow_count,
 --today
 SUM(((c.queue in (2,3) and
 (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt}) or (c.queue in (1,4) and
 (((case when c.odue != 0 then c.odue else c.due end) - {next_anki_day_start}) / 86400) = 0)))
 as today,
 -- suspended
 SUM(CASE
 WHEN (c.did IS NOT NULL AND c.queue = -1)
 THEN 1
 ELSE 0
 END) AS suspended_count,

 -- buried (NEW for item 104)
 SUM(CASE
 WHEN (c.did IS NOT NULL AND c.queue in (-2, -3))
 THEN 1
 ELSE 0
 END) AS buried_count,

 -- new
 SUM(CASE
 WHEN (c.type = 0 and not c.queue in (-1, -2,-3) AND (c.did IS NOT NULL OR (c.odid != 0 AND c.odid IS NOT NULL)))
 THEN 1
 ELSE 0
 END) AS new_count

FROM cards c
GROUP BY c.did;"""

# שאיבת עומס תחזית: כמות כרטיסי חזרה לכל יום בטווח 1-21 ימים קדימה
forecast_query = """
SELECT
    (due - {days_from_crt}) AS days_ahead,
    COUNT(*) AS cnt
FROM cards
WHERE queue IN (2, 3)
  AND due > {days_from_crt}
  AND due <= {days_from_crt} + {forecast_calc_days}
GROUP BY due
ORDER BY due;
"""
