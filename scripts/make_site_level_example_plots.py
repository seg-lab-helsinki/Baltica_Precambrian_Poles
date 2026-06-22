from pathlib import Path
import re
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
FIG = REPO / "figures" / "site_level_examples"

SITE_WORKBOOK_CANDIDATES = [
    DATA / "site_level_data_site_comments_added.xlsx",
    DATA / "site_level_data.xlsx",
    REPO / "site_level_data_site_comments_added.xlsx",
]

MATCH_CANDIDATES = [
    DATA / "pole_sheet_match.csv",
    REPO / "pole_sheet_match.csv",
]


def slugify(s):
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def norm(s):
    return slugify(s)


def find_workbook():
    for p in SITE_WORKBOOK_CANDIDATES:
        if p.exists():
            return p
    print("No site-level workbook found; skipping site-level plots.")
    return None


def find_match_file():
    for p in MATCH_CANDIDATES:
        if p.exists():
            return p
    return None


def read_match_table(path):
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
        if c is None:
            continue
        key = norm(c)
        if key in cols:
            return cols[key]
    return None


def equal_area_xy(dec_deg, inc_deg):
    dec = np.radians(dec_deg)
    inc = np.radians(np.abs(inc_deg))
    r = np.sqrt(2) * np.sin((np.pi / 2 - inc) / 2)
    x = r * np.sin(dec)
    y = r * np.cos(dec)
    return x, y


def draw_stereonet(ax):
    circle = plt.Circle((0, 0), 1, fill=False, linewidth=1.8, color="black")
    ax.add_patch(circle)
    ax.plot([0, 0], [-1, 1], linestyle=":", linewidth=1.0, color="black")
    ax.plot([-1, 1], [0, 0], linestyle=":", linewidth=1.0, color="black")
    for deg in range(0, 360, 10):
        a = np.radians(deg)
        tick_len = 0.955 if deg % 30 else 0.925
        ax.plot([np.sin(a), tick_len * np.sin(a)],
                [np.cos(a), tick_len * np.cos(a)], linewidth=0.8, color="black")
    ax.text(0, 1.10, "N", ha="center", va="center", fontsize=11)
    ax.text(1.10, 0, "E", ha="center", va="center", fontsize=11)
    ax.text(0, -1.10, "S", ha="center", va="center", fontsize=11)
    ax.text(-1.10, 0, "W", ha="center", va="center", fontsize=11)
    ax.set_aspect("equal")
    ax.set_xlim(-1.20, 1.20)
    ax.set_ylim(-1.20, 1.20)
    ax.axis("off")


def make_stereonet(df, dec_col, inc_col, out_png, title):
    df = df.copy()
    df[dec_col] = pd.to_numeric(df[dec_col], errors="coerce")
    df[inc_col] = pd.to_numeric(df[inc_col], errors="coerce")
    df = df.dropna(subset=[dec_col, inc_col])

    if df.empty:
        print(f"No direction data for {title}")
        return

    down = df[df[inc_col] >= 0]
    up = df[df[inc_col] < 0]

    fig, ax = plt.subplots(figsize=(7, 7))
    draw_stereonet(ax)

    if not down.empty:
        x, y = equal_area_xy(down[dec_col], down[inc_col])
        ax.scatter(x, y, marker="o", s=38, color="#1f77b4",
                   edgecolors="#1f77b4", label=f"Positive inc. (N={len(down)})")

    if not up.empty:
        x, y = equal_area_xy(up[dec_col], up[inc_col])
        ax.scatter(x, y, marker="o", s=38, facecolors="white",
                   edgecolors="black", linewidths=1.1,
                   label=f"Negative inc. (N={len(up)})")

    ax.set_title(title, fontsize=13, pad=12)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.10), ncol=1, frameon=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def lonlat_to_unit(lon_deg, lat_deg):
    lon = np.radians(lon_deg)
    lat = np.radians(lat_deg)
    x = np.cos(lat) * np.cos(lon)
    y = np.cos(lat) * np.sin(lon)
    z = np.sin(lat)
    return np.vstack([x, y, z]).T


def unit_to_lonlat(v):
    x, y, z = v
    lon = (np.degrees(np.arctan2(y, x)) + 360) % 360
    hyp = np.sqrt(x*x + y*y)
    lat = np.degrees(np.arctan2(z, hyp))
    return lon, lat


def fisher_mean_pole(lons, lats):
    vecs = lonlat_to_unit(np.asarray(lons), np.asarray(lats))
    Rvec = vecs.sum(axis=0)
    R = np.linalg.norm(Rvec)
    n = len(vecs)
    mean = Rvec / R
    lon, lat = unit_to_lonlat(mean)

    if n > 1 and R < n:
        k = (n - 1) / (n - R)
        try:
            a95 = np.degrees(np.arccos(1 - ((n - R) / R) * ((20 ** (1 / (n - 1))) - 1)))
        except Exception:
            a95 = np.nan
    else:
        k = np.nan
        a95 = np.nan
    return {"lon": lon, "lat": lat, "n": n, "R": R, "k": k, "a95": a95}


def great_circle_endpoint(lon_deg, lat_deg, distance_deg, bearing_deg):
    lon1 = math.radians(lon_deg)
    lat1 = math.radians(lat_deg)
    d = math.radians(distance_deg)
    b = math.radians(bearing_deg)

    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(b))
    lon2 = lon1 + math.atan2(
        math.sin(b) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2),
    )
    lon2 = (math.degrees(lon2) + 540) % 360 - 180
    lat2 = math.degrees(lat2)
    return lon2, lat2


def a95_circle(lon_deg, lat_deg, radius_deg, n=361):
    bearings = np.linspace(0, 360, n)
    pts = [great_circle_endpoint(lon_deg, lat_deg, radius_deg, b) for b in bearings]
    return np.array([p[0] for p in pts]), np.array([p[1] for p in pts])


def to_cartopy_lon(lon):
    return ((np.asarray(lon) + 180) % 360) - 180


def make_vgp_globe(df, lat_col, lon_col, out_png, title):
    df = df.copy()
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])

    if df.empty:
        print(f"No VGP data for {title}")
        return

    mean = fisher_mean_pole(df[lon_col].values, df[lat_col].values)

    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except Exception as e:
        print(f"Cartopy unavailable, skipping globe plot: {e}")
        return

    central_lon = to_cartopy_lon(mean["lon"])
    central_lat = float(mean["lat"])

    fig = plt.figure(figsize=(8, 8))
    ax = plt.axes(projection=ccrs.Orthographic(central_longitude=central_lon, central_latitude=central_lat))
    ax.set_global()

    ax.add_feature(cfeature.OCEAN, facecolor="white", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor="#d7bd91", edgecolor="black", linewidth=0.45, zorder=1)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.7, edgecolor="black", zorder=2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.35, edgecolor="black", alpha=0.8, zorder=2)
    ax.gridlines(color="black", linestyle=":", linewidth=0.75, alpha=0.9)

    # VGPs
    ax.scatter(to_cartopy_lon(df[lon_col].values), df[lat_col].values,
               s=38, color="#4969d8", edgecolor="white", linewidth=0.5,
               alpha=0.85, transform=ccrs.PlateCarree(), zorder=5, label="Site VGPs")

    # A95 circle and mean pole
    if not np.isnan(mean["a95"]) and mean["a95"] > 0:
        clons, clats = a95_circle(float(mean["lon"]), float(mean["lat"]), float(mean["a95"]))
        ax.fill(clons, clats, transform=ccrs.PlateCarree(),
                facecolor="red", alpha=0.20, edgecolor="red", linewidth=1.2, zorder=4)
        ax.plot(clons, clats, transform=ccrs.PlateCarree(),
                color="red", linewidth=1.2, zorder=6)

    ax.scatter([to_cartopy_lon(mean["lon"])], [mean["lat"]],
               s=80, color="red", edgecolor="black", linewidth=0.8,
               transform=ccrs.PlateCarree(), zorder=7, label="Mean pole")

    title2 = f"{title}\nmean pole {mean['lat']:.1f}°N, {mean['lon']:.1f}°E; A95 {mean['a95']:.1f}°; N={int(mean['n'])}"
    ax.set_title(title2, fontsize=12)
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_vgp_xy_plot(df, lat_col, lon_col, out_png, title):
    df = df.copy()
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])

    if df.empty:
        print(f"No VGP data for {title}")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(df[lon_col], df[lat_col], marker="o")
    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("VGP longitude (°E)")
    ax.set_ylabel("VGP latitude (°)")
    ax.set_title(title)
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


def make_deenen_plot(df, lat_col, lon_col, out_png, title):
    df = df.copy()
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])

    if len(df) < 2:
        print(f"Too few VGPs for Deenen plot: {title}")
        return

    mean = fisher_mean_pole(df[lon_col].values, df[lat_col].values)
    n = mean["n"]
    a95 = mean["a95"]

    xs = np.arange(2, 81)
    a95_min = 12 * xs ** (-0.4)
    a95_max = 82 * xs ** (-0.63)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(xs, a95_min, a95_max, alpha=0.25, label="Acceptable range")
    ax.plot(xs, a95_min, linestyle="--", label=r"$A_{95,min}$")
    ax.plot(xs, a95_max, linestyle="--", label=r"$A_{95,max}$")
    ax.scatter([n], [a95], marker="*", s=220, color="red", label="pole", zorder=5)
    ax.set_xlim(2, 80)
    ax.set_ylim(0, max(25, np.nanmax(a95_max[:20]) + 2))
    ax.set_xlabel("Number of sites (N)")
    ax.set_ylabel(r"$A_{95}$ (°)")
    ax.set_title(f"{title}: Deenen et al. (2011) test")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


def load_examples_from_match():
    path = find_match_file()
    if path is None:
        return []

    df = read_match_table(path)
    df.columns = [str(c).strip() for c in df.columns]
    sheet_col = pick_col(df, ["sheet_name", "matched_sheet", "sheet", "excel_sheet"])
    pole_col = pick_col(df, ["pole_id", "id"])
    if sheet_col is None:
        return []

    examples = []
    for _, row in df.iterrows():
        sheet = row.get(sheet_col)
        if pd.isna(sheet) or str(sheet).strip() == "":
            continue
        pole_id = row.get(pole_col, sheet) if pole_col else sheet
        examples.append({"pole_id": str(pole_id), "sheet_name": str(sheet)})
    return examples


def main():
    workbook = find_workbook()
    if workbook is None:
        return

    xl = pd.ExcelFile(workbook)
    existing_sheets = set(xl.sheet_names)

    examples = load_examples_from_match()
    if not examples:
        examples = [{"pole_id": s, "sheet_name": s} for s in xl.sheet_names]

    FIG.mkdir(parents=True, exist_ok=True)

    for ex in examples:
        sheet = ex["sheet_name"]
        if sheet not in existing_sheets:
            print(f"Sheet not found, skipping: {sheet}")
            continue

        df = pd.read_excel(workbook, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]

        dec_col = pick_col(df, ["dir_dec", "dec_acs", "Dec (TI)", "Dec", "D"])
        inc_col = pick_col(df, ["dir_inc", "inc_acs", "Inc (TI)", "Inc", "I"])
        vgp_lat_col = pick_col(df, ["vgp_lat", "VGP_lat", "Plat", "P_LAT"])
        vgp_lon_col = pick_col(df, ["vgp_lon", "VGP_long", "VGP_lon", "Plon", "P_LONG"])

        out_dir = FIG / slugify(sheet)
        out_dir.mkdir(parents=True, exist_ok=True)

        if dec_col and inc_col:
            make_stereonet(
                df, dec_col, inc_col,
                out_dir / "direction_stereonet.png",
                f"{sheet}: site directions",
            )
        else:
            print(f"No direction columns found for {sheet}")

        if vgp_lat_col and vgp_lon_col:
            make_vgp_xy_plot(
                df, vgp_lat_col, vgp_lon_col,
                out_dir / "vgp_distribution.png",
                f"{sheet}: VGP distribution",
            )
            make_vgp_globe(
                df, vgp_lat_col, vgp_lon_col,
                out_dir / "vgp_globe.png",
                f"{sheet}: VGPs and mean pole",
            )
            make_deenen_plot(
                df, vgp_lat_col, vgp_lon_col,
                out_dir / "deenen_psv.png",
                f"{sheet}",
            )
        else:
            print(f"No VGP columns found for {sheet}")

    print("Finished site-level example plots.")


if __name__ == "__main__":
    main()
