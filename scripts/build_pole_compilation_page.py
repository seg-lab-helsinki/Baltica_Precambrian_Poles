from pathlib import Path
import html
import re

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
INPUT_CSV = REPO / "data" / "Baltica_poles.csv"
OUTPUT_HTML = REPO / "pages" / "pole_compilation.html"


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def read_csv_flexible(path):
    # Handles the current Baltica_poles.csv format:
    # semicolon-separated and sometimes cp1252/latin1 because of Scandinavian characters.
    encodings = ["utf-8-sig", "cp1252", "latin1"]
    separators = [";", ",", "\t"]

    for enc in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(
                    path,
                    sep=sep,
                    engine="python",
                    encoding=enc,
                    on_bad_lines="skip"
                )
                if len(df.columns) >= 4:
                    print(f"Read {path} using encoding={enc}, separator={repr(sep)}")
                    return df
            except Exception:
                pass

    raise ValueError(f"Could not read CSV file correctly: {path}")


def pick_col(df, names, required=False):
    lookup = {norm(c): c for c in df.columns}
    for n in names:
        key = norm(n)
        if key in lookup:
            return lookup[key]
    if required:
        raise KeyError(f"Missing required column. Tried {names}. Available: {list(df.columns)}")
    return None


def safe(x):
    if pd.isna(x):
        return ""
    return html.escape(str(x))


def fmt_num(x, nd=1):
    try:
        if pd.isna(x):
            return ""
        v = float(x)
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.{nd}f}"
    except Exception:
        return safe(x)


def find_assessment_page(unit, age=None):
    pole_dir = REPO / "pole_assessments"
    if not pole_dir.exists():
        return ""

    u = norm(unit)
    hits = []
    for f in pole_dir.glob("*.html"):
        stem = norm(f.stem)
        if u and u in stem:
            hits.append(f)
    if hits:
        return "../pole_assessments/" + sorted(hits)[0].name

    # fallback: try a shorter unit token
    tokens = [t for t in u.split("_") if len(t) > 3]
    if len(tokens) >= 2:
        for f in pole_dir.glob("*.html"):
            stem = norm(f.stem)
            if all(t in stem for t in tokens[:2]):
                return "../pole_assessments/" + f.name
    return ""


def badge(value, css_class=""):
    return f'<span class="badge {css_class}">{safe(value)}</span>'


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Cannot find {INPUT_CSV}")

    df = read_csv_flexible(INPUT_CSV)
    df.columns = [str(c).strip() for c in df.columns]

    c_terrane = pick_col(df, ["Terrane", "terrane", "craton"])
    c_unit = pick_col(df, ["Unit", "ROCKNAME", "rockname", "unit", "name"], required=True)
    c_age = pick_col(df, ["Age_Ma", "age_ma", "age"], required=True)
    c_age_min = pick_col(df, ["age_min", "Age_min", "low_age", "lomagage"])
    c_age_max = pick_col(df, ["age_max", "Age_max", "high_age", "himagage"])
    c_rating = pick_col(df, ["Rating", "rating", "grade"], required=True)
    c_slon = pick_col(df, ["S_LONG", "site_lon", "S_lon", "lon"], required=True)
    c_slat = pick_col(df, ["S_LAT", "site_lat", "S_lat", "lat"], required=True)
    c_plon = pick_col(df, ["P_LONG", "Plon", "pole_lon"], required=True)
    c_plat = pick_col(df, ["P_LAT", "Plat", "pole_lat"], required=True)
    c_a95 = pick_col(df, ["A95", "a95", "alpha95"])
    c_ref = pick_col(df, ["Reference", "reference", "authors", "Authors"])

    for c in [c_age, c_age_min, c_age_max, c_slon, c_slat, c_plon, c_plat, c_a95]:
        if c:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(how="all").copy()
    df = df.sort_values(by=c_age, ascending=True, na_position="last")

    rows = []
    for _, r in df.iterrows():
        unit = r[c_unit]
        link = find_assessment_page(unit, r[c_age])
        unit_html = safe(unit)
        if link:
            unit_html = f'<a href="{link}">{unit_html}</a>'

        grade = str(r[c_rating]).strip()
        grade_class = "grade-a" if grade.upper().startswith("A") else "grade-b" if grade.upper().startswith("B") else "grade-c"

        rows.append(f"""
        <tr>
          <td>{safe(r[c_terrane]) if c_terrane else ""}</td>
          <td class="unit">{unit_html}</td>
          <td>{fmt_num(r[c_age], 0)}</td>
          <td>{fmt_num(r[c_age_min], 0) if c_age_min else ""}</td>
          <td>{fmt_num(r[c_age_max], 0) if c_age_max else ""}</td>
          <td>{badge(grade, grade_class)}</td>
          <td>{fmt_num(r[c_slon], 2)}</td>
          <td>{fmt_num(r[c_slat], 2)}</td>
          <td>{fmt_num(r[c_plon], 2)}</td>
          <td>{fmt_num(r[c_plat], 2)}</td>
          <td>{fmt_num(r[c_a95], 1) if c_a95 else ""}</td>
          <td class="ref">{safe(r[c_ref]) if c_ref else ""}</td>
        </tr>
        """)

    n = len(df)

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Pole compilation — Baltica Precambrian Poles</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ margin:0; font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f4f6fb; color:#07152f; }}
    .layout {{ display:grid; grid-template-columns:290px 1fr; min-height:100vh; }}
    nav {{ background:white; border-right:1px solid #d8e0ee; padding:28px 24px; position:sticky; top:0; height:100vh; box-sizing:border-box; overflow-y:auto; }}
    nav h1 {{ font-size:24px; line-height:1.05; color:#0c3c90; margin:0 0 8px 0; text-transform:uppercase; letter-spacing:.02em; }}
    nav .subtitle {{ font-weight:700; font-size:14px; margin-bottom:34px; }}
    nav a {{ display:block; color:#06152f; text-decoration:none; font-weight:650; padding:10px 12px; border-radius:10px; margin:3px 0; }}
    nav a.active {{ color:#1455d9; background:#dce9ff; }}
    main {{ padding:48px 56px 70px; max-width:1320px; }}
    h2 {{ font-size:42px; margin:0 0 18px 0; letter-spacing:-0.03em; }}
    .intro {{ font-size:18px; line-height:1.55; max-width:950px; margin-bottom:22px; }}
    .card {{ background:white; border-radius:22px; padding:28px; box-shadow:0 14px 38px rgba(15,23,42,.08); }}
    .table-wrap {{ overflow:auto; border:1px solid #d8e0ee; border-radius:14px; }}
    table {{ border-collapse:collapse; width:100%; min-width:1120px; font-size:14px; }}
    th {{ background:#eef3fa; text-align:left; padding:12px 10px; position:sticky; top:0; z-index:1; }}
    td {{ padding:11px 10px; border-top:1px solid #e2e8f0; vertical-align:top; }}
    tr:hover {{ background:#f8fbff; }}
    .unit a {{ color:#075ec9; text-decoration:underline; }}
    .ref {{ max-width:310px; }}
    .badge {{ display:inline-block; padding:4px 10px; border-radius:999px; font-weight:800; }}
    .grade-a {{ background:#d6f7df; color:#085b20; }}
    .grade-b {{ background:#dbeafe; color:#123f8c; }}
    .grade-c {{ background:#fff1c2; color:#725100; }}
    .count {{ color:#526174; margin-top:14px; font-size:14px; }}
    input {{ width:100%; box-sizing:border-box; padding:12px 14px; border:1px solid #cbd5e1; border-radius:12px; font-size:16px; margin-bottom:16px; }}
  </style>
</head>
<body>
<div class="layout">
  <nav>
    <h1>Baltica<br>Precambrian Poles</h1>
    <div class="subtitle">Working database prototype</div>
    <a href="../index.html">Home / overview</a>
    <a href="interactive_pole_map.html">Interactive pole map</a>
    <a class="active" href="pole_compilation.html">Pole compilation</a>
    <a href="paleolatitude.html">Baltica paleolatitude through time</a>
    <a href="revisions_and_additions.html">Revisions and additions</a>
    <a href="../pole_assessments/">Pole Assessments</a>
    <a href="resources.html">Resources</a>
  </nav>
  <main>
    <h2>Pole compilation</h2>
    <p class="intro">
      Working Baltica Precambrian pole compilation generated directly from
      <code>data/Baltica_poles.csv</code>. The table is regenerated automatically
      whenever the master CSV is updated.
    </p>
    <section class="card">
      <input id="search" placeholder="Search units, terranes, references, ages, grades..." onkeyup="filterTable()">
      <div class="table-wrap">
        <table id="poleTable">
          <thead>
            <tr>
              <th>Terrane</th>
              <th>Unit</th>
              <th>Age Ma</th>
              <th>Age min</th>
              <th>Age max</th>
              <th>Rating</th>
              <th>Site lon</th>
              <th>Site lat</th>
              <th>Plon</th>
              <th>Plat</th>
              <th>A95</th>
              <th>Reference</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
      <p class="count" id="count">Showing {n} of {n} poles.</p>
    </section>
  </main>
</div>

<script>
function filterTable() {{
  const q = document.getElementById("search").value.toLowerCase();
  const rows = document.querySelectorAll("#poleTable tbody tr");
  let shown = 0;
  rows.forEach(row => {{
    const match = row.innerText.toLowerCase().includes(q);
    row.style.display = match ? "" : "none";
    if (match) shown++;
  }});
  document.getElementById("count").innerText = `Showing ${{shown}} of {n} poles.`;
}}
</script>
</body>
</html>
"""

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT_HTML} with {n} poles.")


if __name__ == "__main__":
    main()
