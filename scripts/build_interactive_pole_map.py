from pathlib import Path
import html
import re

import pandas as pd
import folium
from branca.colormap import linear
from branca.element import MacroElement, Template


REPO = Path(__file__).resolve().parents[1]
INPUT_CSV = REPO / "data" / "Baltica_poles.csv"
OUTPUT_HTML = REPO / "pages" / "interactive_pole_map.html"


class MapLegend(MacroElement):
    def __init__(self):
        super().__init__()
        self._name = "MapLegend"
        self._template = Template("""
        {% macro script(this, kwargs) %}
        var legend = L.control({position: 'bottomleft'});
        legend.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'map-legend');
            div.innerHTML = `
                <div style="
                    background: rgba(255,255,255,0.94);
                    padding: 12px 14px;
                    border: 1px solid #888;
                    border-radius: 6px;
                    font-size: 13px;
                    line-height: 1.45;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.25);
                    min-width: 190px;
                ">
                    <b>Sampling localities</b><br>

                    <span style="
                        display:inline-block;
                        width:13px;
                        height:13px;
                        background:#777;
                        border:1.6px solid #111;
                        transform:rotate(45deg);
                        margin-right:7px;
                    "></span>
                    A-grade<br>

                    <span style="
                        display:inline-block;
                        width:13px;
                        height:13px;
                        background:#777;
                        border:1.6px solid #111;
                        margin-right:7px;
                    "></span>
                    B-grade<br>

                    <span style="
                        display:inline-block;
                        width:13px;
                        height:13px;
                        border-radius:50%;
                        background:#777;
                        border:1.6px solid #111;
                        margin-right:7px;
                    "></span>
                    C+-grade<br>

                    <span style="font-size:12px;color:#444;">
                        Colour = nominal age
                    </span>
                </div>
            `;
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        legend.addTo({{this._parent.get_name()}});
        {% endmacro %}
        """)


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def read_csv_flexible(path):
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
                    on_bad_lines="skip",
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
        raise KeyError(
            f"Missing required column. Tried {names}. Available columns: {list(df.columns)}"
        )

    return None


def safe(x):
    return "—" if pd.isna(x) else html.escape(str(x))


def num(x, nd=1):
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x):.{nd}f}"
    except Exception:
        return safe(x)


def marker_html(color, grade):
    """
    Marker convention matched to manuscript geology map:
        A-grade  = diamond
        B-grade  = square
        C+-grade = circle
    """
    g = str(grade).upper().strip().replace(" ", "")

    # A-grade = diamond
    if g.startswith("A"):
        return f"""
        <div style="
            width:14px;
            height:14px;
            background:{color};
            border:1.8px solid #111;
            transform:rotate(45deg);
            opacity:.95;
        "></div>
        """

    # B-grade = square
    if g.startswith("B"):
        return f"""
        <div style="
            width:14px;
            height:14px;
            background:{color};
            border:1.8px solid #111;
            opacity:.95;
        "></div>
        """

    # C+ grade = circle
    return f"""
    <div style="
        width:14px;
        height:14px;
        background:{color};
        border:1.8px solid #111;
        border-radius:50%;
        opacity:.95;
    "></div>
    """


def assessment_link(pole_id="", unit="", age=""):
    """
    Try to link a marker to a pole-assessment page.

    The current Baltica_poles.csv may not contain pole_id, so this function
    also searches by normalized unit name.
    """
    pole_dir = REPO / "pole_assessments"
    if not pole_dir.exists():
        return ""

    html_files = list(pole_dir.glob("*.html"))

    search_terms = []

    if pole_id and str(pole_id).lower() != "nan":
        search_terms.append(norm(pole_id))

    if unit and str(unit).lower() != "nan":
        unit_slug = norm(unit)
        search_terms.append(unit_slug)

        # Also try a simplified version without common suffix words.
        simplified = re.sub(r"(_c|_precise|_group_a|_group_b)$", "", unit_slug)
        if simplified and simplified != unit_slug:
            search_terms.append(simplified)

    # First: exact or strong filename match
    for term in search_terms:
        if not term:
            continue

        for f in html_files:
            if term in norm(f.stem):
                return "../pole_assessments/" + f.name

    return ""


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Cannot find {INPUT_CSV}")

    df = read_csv_flexible(INPUT_CSV)
    df.columns = [str(c).strip() for c in df.columns]

    c_unit = pick_col(df, ["Unit", "ROCKNAME", "rockname", "unit", "name"])
    c_age = pick_col(df, ["Age_Ma", "age_ma", "age", "nominal_age_ma"], required=True)
    c_grade = pick_col(df, ["Rating", "rating", "grade", "Grade"], required=True)

    # IMPORTANT: these are sampling/locality coordinates, not paleomagnetic pole coordinates.
    c_slat = pick_col(
        df,
        ["S_LAT", "site_lat", "Site_lat", "SLAT", "lat", "sampling_lat"],
        required=True,
    )
    c_slon = pick_col(
        df,
        ["S_LONG", "site_lon", "Site_lon", "SLONG", "lon", "lng", "sampling_lon"],
        required=True,
    )

    c_plat = pick_col(df, ["P_LAT", "Plat", "pole_lat", "paleopole_lat"])
    c_plon = pick_col(df, ["P_LONG", "Plon", "pole_lon", "paleopole_lon"])
    c_a95 = pick_col(df, ["A95", "a95", "alpha95"])
    c_ref = pick_col(df, ["Reference", "reference", "Authors", "authors"])
    c_pid = pick_col(df, ["pole_id", "id"])

    for c in [c_age, c_slat, c_slon, c_plat, c_plon, c_a95]:
        if c:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=[c_slat, c_slon]).copy()

    if df.empty:
        raise ValueError("No valid site coordinates found in Baltica_poles.csv")

    m = folium.Map(
        location=[df[c_slat].median(), df[c_slon].median()],
        zoom_start=4,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=True,
    )

    cmap = None
    if df[c_age].notna().any():
        cmap = linear.viridis.scale(float(df[c_age].min()), float(df[c_age].max()))
        cmap.caption = "Nominal age (Ma)"
        cmap.add_to(m)

    layer = folium.FeatureGroup(name="Paleomagnetic poles", show=True)

    for _, row in df.iterrows():
        color = (
            cmap(float(row[c_age]))
            if cmap is not None and pd.notna(row[c_age])
            else "#666666"
        )

        unit = row[c_unit] if c_unit else row[c_pid] if c_pid else "Pole"
        pole_id = str(row[c_pid]).strip() if c_pid else ""

        link = assessment_link(
            pole_id=pole_id,
            unit=str(unit),
            age=str(row[c_age]) if pd.notna(row[c_age]) else "",
        )

        link_html = (
            f'<p><a href="{link}" target="_blank">Open pole assessment page</a></p>'
            if link
            else ""
        )

        popup = f"""
        <div style="font-size:13px;line-height:1.35;min-width:260px;">
          <h4 style="margin:0 0 6px 0;">{safe(unit)}</h4>
          <b>Age:</b> {num(row[c_age], 0)} Ma<br>
          <b>Grade:</b> {safe(row[c_grade])}<br>
          <b>Sampling locality:</b> {num(row[c_slat], 3)}°N, {num(row[c_slon], 3)}°E<br>
          <b>Pole:</b> Plat {num(row[c_plat], 2) if c_plat else "—"}°,
          Plon {num(row[c_plon], 2) if c_plon else "—"}°E<br>
          <b>A95:</b> {num(row[c_a95], 1) if c_a95 else "—"}°<br>
          <b>Reference:</b> {safe(row[c_ref]) if c_ref else "—"}
          {link_html}
        </div>
        """

        folium.Marker(
            location=[float(row[c_slat]), float(row[c_slon])],
            icon=folium.DivIcon(
                html=marker_html(color, row[c_grade]),
                icon_size=(18, 18),
                icon_anchor=(9, 9),
            ),
            popup=folium.Popup(popup, max_width=380),
            tooltip=safe(unit),
        ).add_to(layer)

    layer.add_to(m)
    m.get_root().add_child(MapLegend())
    folium.LayerControl(collapsed=False).add_to(m)

    m.get_root().html.add_child(
        folium.Element(
            """
    <style>
    .folium-map {
        width: 100% !important;
        height: 720px !important;
        min-height: 720px !important;
    }
    .leaflet-container {
        width: 100% !important;
        height: 720px !important;
    }
    </style>
    """
        )
    )

    map_html = m.get_root().render()

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Interactive pole map — Baltica Precambrian Poles</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{
      margin:0;
      font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background:#f4f6fb;
      color:#07152f;
    }}
    .layout {{
      display:grid;
      grid-template-columns:290px 1fr;
      min-height:100vh;
    }}
    nav {{
      background:white;
      border-right:1px solid #d8e0ee;
      padding:28px 24px;
      position:sticky;
      top:0;
      height:100vh;
      box-sizing:border-box;
      overflow-y:auto;
    }}
    nav h1 {{
      font-size:24px;
      line-height:1.05;
      color:#0c3c90;
      margin:0 0 8px 0;
      text-transform:uppercase;
      letter-spacing:.02em;
    }}
    nav .subtitle {{
      font-weight:700;
      font-size:14px;
      margin-bottom:34px;
    }}
    nav a {{
      display:block;
      color:#06152f;
      text-decoration:none;
      font-weight:650;
      padding:10px 12px;
      border-radius:10px;
      margin:3px 0;
    }}
    nav a.active {{
      color:#1455d9;
      background:#dce9ff;
    }}
    main {{
      padding:48px 56px 70px;
      max-width:1250px;
    }}
    h2 {{
      font-size:42px;
      margin:0 0 24px 0;
      letter-spacing:-0.03em;
    }}
    .card {{
      background:white;
      border-radius:22px;
      padding:28px;
      box-shadow:0 14px 38px rgba(15,23,42,.08);
      margin-bottom:28px;
    }}
    .intro {{
      font-size:18px;
      line-height:1.65;
      max-width:1000px;
      margin-bottom:24px;
    }}
  </style>
</head>
<body>
<div class="layout">
  <nav>
    <h1>Baltica<br>Precambrian Poles</h1>
    <div class="subtitle">Working database prototype</div>
    <a href="../index.html">Home / overview</a>
    <a class="active" href="interactive_pole_map.html">Interactive pole map</a>
    <a href="pole_compilation.html">Pole compilation</a>
    <a href="paleolatitude.html">Baltica paleolatitude through time</a>
    <a href="revisions_and_additions.html">Revisions and additions</a>
    <a href="../pole_assessments/">Pole Assessments</a>
    <a href="resources.html">Resources</a>
  </nav>
  <main>
    <h2>Interactive pole map</h2>
    <p class="intro">
      Interactive map of the Baltica Precambrian pole compilation. Markers show
      present-day sampling localities from the master pole table. Marker colour
      indicates nominal age, and marker shape indicates reliability grade:
      diamond = A-grade, square = B-grade, circle = C+-grade. Click a marker
      to view pole information and links to available pole-assessment pages.
    </p>
    <section class="card">
      {map_html}
    </section>
  </main>
</div>
</body>
</html>"""

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(page, encoding="utf-8")

    print(f"Wrote {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
