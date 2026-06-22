from pathlib import Path
import html
import re
import sys

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
ASSESS = REPO / "pole_assessments"

WORKBOOK = DATA / "site_level_data_site_comments_added.xlsx"
MATCH = DATA / "pole_sheet_match.csv"

PREFERRED_COLUMNS = [
    "site",
    "dir_dec",
    "dir_inc",
    "dir_k",
    "dir_alpha95",
    "dir_n_samples",
    "vgp_lat",
    "vgp_lon",
    "authors",
    "comment",
]


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def read_match_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, encoding="utf-8-sig")
            if len(df.columns) >= 2:
                return df
        except Exception:
            pass
    return pd.read_csv(path, encoding="utf-8-sig")


def pick_col(df, candidates):
    cols = {norm(c): c for c in df.columns}
    for c in candidates:
        key = norm(c)
        if key in cols:
            return cols[key]
    return None


def find_matching_html(pole_id, unit, html_files):
    targets = [norm(pole_id), norm(unit)]
    targets = [t for t in targets if t and t != "nan"]

    for t in targets:
        for f in html_files:
            if t and t in norm(f.stem):
                return f

    for f in html_files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        low = norm(txt)
        for t in targets:
            if t and t in low:
                return f

    return None


def clean_dataframe_for_html(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    keep = []
    for c in df.columns:
        cs = str(c).strip()
        if not cs:
            continue
        if cs.lower().startswith("unnamed"):
            continue
        keep.append(c)
    df = df[keep]

    rename = {}
    for c in df.columns:
        cn = norm(c)
        if cn in ["dec_ti", "dec", "d", "dir_dec_deg"]:
            rename[c] = "dir_dec"
        elif cn in ["inc_ti", "inc", "i", "dir_inc_deg"]:
            rename[c] = "dir_inc"
        elif cn in ["n", "dir_n", "n_samples"]:
            rename[c] = "dir_n_samples"
        elif cn in ["k"]:
            rename[c] = "dir_k"
        elif cn in ["a95", "alpha95", "dir_a95"]:
            rename[c] = "dir_alpha95"
        elif cn in ["vgp_long", "vgp_lon", "p_long", "plon"]:
            rename[c] = "vgp_lon"
        elif cn in ["vgp_lat", "p_lat", "plat"]:
            rename[c] = "vgp_lat"
        elif cn in ["authors", "author", "reference", "source"]:
            rename[c] = "authors"
        elif cn in ["comment", "comments", "notes"]:
            rename[c] = "comment"
        elif cn in ["site", "site_name", "locality"]:
            rename[c] = "site"

    df = df.rename(columns=rename)
    df = df.loc[:, ~df.columns.duplicated()]
    cols = [c for c in PREFERRED_COLUMNS if c in df.columns]
    cols += [c for c in df.columns if c not in cols]
    return df[cols]


def fmt_value(v):
    if pd.isna(v):
        return ""
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-10:
            return str(int(round(v)))
        return f"{v:.6g}"
    return str(v)


def dataframe_to_html_table(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p><em>No site-level rows currently available for this matched sheet.</em></p>'
    parts = ['<div class="table-wrap">', '<table>', '<thead><tr>']
    for c in df.columns:
        parts.append(f"<th>{html.escape(str(c))}</th>")
    parts.append('</tr></thead>')
    parts.append('<tbody>')
    for _, row in df.iterrows():
        parts.append('<tr>')
        for c in df.columns:
            parts.append(f"<td>{html.escape(fmt_value(row[c]))}</td>")
        parts.append('</tr>')
    parts.append('</tbody>')
    parts.append('</table>')
    parts.append('</div>')
    return "\n".join(parts)


def build_site_level_card(sheet_name, df):
    table = dataframe_to_html_table(df)
    return f'''<section class="card" id="site-level-data">
  <h2>Site-level data</h2>
  {table}
  <p class="small-note">
    Source workbook: <code>data/site_level_data_site_comments_added.xlsx</code>;
    sheet: <strong>{html.escape(sheet_name)}</strong>.
    This table is regenerated automatically from the workbook.
  </p>
</section>'''


def build_site_level_figure_cards(sheet_name):
    slug = norm(sheet_name)
    direction_rel = f"../figures/site_level_examples/{slug}/direction_stereonet.png"
    vgp_globe_rel = f"../figures/site_level_examples/{slug}/vgp_globe.png"
    deenen_rel = f"../figures/site_level_examples/{slug}/deenen_psv.png"
    return f'''
<section class="card" id="site-level-direction-scatter">
  <h2>Site-level direction scatter</h2>
  <p>
    Tilt-corrected site directions for <strong>{html.escape(sheet_name)}</strong>.
    Filled and open symbols distinguish positive and negative inclinations.
    This plot shows the scatter of individual site directions behind the mean pole.
  </p>
  <figure>
    <img src="{direction_rel}"
         alt="{html.escape(sheet_name)} site direction stereonet"
         style="width:100%; max-width:850px; border-radius:12px;">
    <figcaption>
      Site-level direction scatter for {html.escape(sheet_name)}.
      No polarity unification is applied in this diagnostic plot.
    </figcaption>
  </figure>
</section>

<section class="card" id="site-level-vgp-globe">
  <h2>Site-level VGPs and mean pole</h2>
  <p>
    Site-level VGPs are plotted on an orthographic globe together with the Fisher mean
    pole and its circular A95 confidence region. This is the Laurentia-style view needed
    to inspect the spatial scatter of the site poles.
  </p>
  <figure>
    <img src="{vgp_globe_rel}"
         alt="{html.escape(sheet_name)} VGP globe"
         style="width:100%; max-width:850px; border-radius:12px;">
    <figcaption>
      Site-level VGPs, mean pole, and A95 confidence circle for {html.escape(sheet_name)}.
    </figcaption>
  </figure>
</section>

<section class="card" id="site-level-psv-deenen">
  <h2>Paleosecular variation</h2>
  <p>
    The Deenen et al. (2011) diagnostic compares the pole A95 with the expected range
    for the number of site-level VGPs. This provides a first-order PSV-style check.
  </p>
  <figure>
    <img src="{deenen_rel}"
         alt="{html.escape(sheet_name)} Deenen PSV diagnostic"
         style="width:100%; max-width:850px; border-radius:12px;">
    <figcaption>
      Deenen-style A95 versus number-of-sites diagnostic for {html.escape(sheet_name)}.
    </figcaption>
  </figure>
</section>'''


def replace_section_by_id(page_text, section_id, replacement):
    pattern = re.compile(
        rf'<section[^>]*id=["\']{re.escape(section_id)}["\'][^>]*>.*?</section>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    if pattern.search(page_text):
        return pattern.sub(replacement, page_text, count=1)
    return page_text


def replace_site_level_content(page_text, new_card, figure_cards):
    old = page_text
    page_text = replace_section_by_id(page_text, "site-level-data", new_card)

    if page_text == old:
        h2 = re.search(r'<h2>\s*Site-level data\s*</h2>', page_text, flags=re.IGNORECASE)
        if h2:
            start = page_text.rfind("<section", 0, h2.start())
            if start == -1:
                start = h2.start()
            end = page_text.find("</section>", h2.end())
            if end != -1:
                end += len("</section>")
                page_text = page_text[:start] + new_card + page_text[end:]
        else:
            pos = page_text.lower().rfind("</main>")
            if pos != -1:
                page_text = page_text[:pos] + "\n" + new_card + "\n" + page_text[pos:]

    for sid in [
        "site-level-direction-scatter",
        "site-level-vgp-distribution",
        "site-level-vgp-globe",
        "site-level-psv-deenen",
    ]:
        page_text = replace_section_by_id(page_text, sid, "")

    site_match = re.search(
        r'<section[^>]*id=["\']site-level-data["\'][^>]*>.*?</section>',
        page_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if site_match:
        end = site_match.end()
        page_text = page_text[:end] + "\n" + figure_cards + "\n" + page_text[end:]
    else:
        pos = page_text.lower().rfind("</main>")
        if pos != -1:
            page_text = page_text[:pos] + "\n" + figure_cards + "\n" + page_text[pos:]

    return page_text


def main():
    if not WORKBOOK.exists():
        print(f"Missing workbook: {WORKBOOK}")
        sys.exit(1)
    if not ASSESS.exists():
        print(f"Missing pole_assessments folder: {ASSESS}")
        sys.exit(1)

    match = read_match_table(MATCH)
    match.columns = [str(c).strip() for c in match.columns]

    pole_col = pick_col(match, ["pole_id", "Pole ID", "id"])
    unit_col = pick_col(match, ["unit", "rockname", "ROCKNAME", "name"])
    sheet_col = pick_col(match, ["sheet_name", "sheet", "excel_sheet", "matched_sheet"])
    if sheet_col is None:
        raise KeyError("pole_sheet_match.csv must contain sheet_name or matched_sheet column.")

    xl = pd.ExcelFile(WORKBOOK)
    sheet_lookup = {norm(s): s for s in xl.sheet_names}
    html_files = list(ASSESS.glob("*.html"))

    updated = 0
    skipped = 0

    for _, row in match.iterrows():
        sheet_requested = row.get(sheet_col, "")
        if pd.isna(sheet_requested) or str(sheet_requested).strip() == "":
            skipped += 1
            continue

        sheet_key = norm(sheet_requested)
        if sheet_key not in sheet_lookup:
            print(f"Sheet not found in workbook, skipping: {sheet_requested}")
            skipped += 1
            continue

        sheet_name = sheet_lookup[sheet_key]
        pole_id = row.get(pole_col, "") if pole_col else ""
        unit = row.get(unit_col, "") if unit_col else sheet_name
        page = find_matching_html(pole_id, unit, html_files)

        if page is None:
            print(f"No matching HTML page found for sheet: {sheet_name} / pole_id: {pole_id}")
            skipped += 1
            continue

        df = pd.read_excel(WORKBOOK, sheet_name=sheet_name)
        df = clean_dataframe_for_html(df)
        new_card = build_site_level_card(sheet_name, df)
        fig_cards = build_site_level_figure_cards(sheet_name)

        old = page.read_text(encoding="utf-8", errors="ignore")
        new = replace_site_level_content(old, new_card, fig_cards)
        if new != old:
            page.write_text(new, encoding="utf-8")
            print(f"Updated page: {page.name} from sheet {sheet_name}")
            updated += 1
        else:
            print(f"No change: {page.name}")

    print(f"Done. Updated {updated} pages; skipped {skipped} rows.")


if __name__ == "__main__":
    main()
