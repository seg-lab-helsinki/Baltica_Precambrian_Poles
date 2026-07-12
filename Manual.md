# Baltica Precambrian Poles webpage — manual from zero

Public webpage for the current project:

`https://ahmedpaleomag.github.io/Baltica_Precambrian_Poles/`

GitHub repository for the current project:

`https://github.com/Ahmedpaleomag/Baltica_Precambrian_Poles`

This manual explains how to create the Baltica Precambrian Poles webpage from zero, and then how to update it later. The main idea is that the scientific data are kept in source files, and the webpage is rebuilt automatically by GitHub Actions.

---

# PART 1 — CREATE THE WEBPAGE FROM ZERO

## 1. Create a GitHub repository

1. Open GitHub.
2. Click the `+` button in the upper-right corner.
3. Choose `New repository`.
4. Enter the repository name, for example:

`Baltica_Precambrian_Poles`

5. Choose `Public` if the webpage should be public.
6. Tick `Add a README file`.
7. Click `Create repository`.

At this point, the repository exists, but the webpage is not ready yet.

---

## 2. Create the basic folder structure

The repository should contain these folders:

```text
data/
pages/
scripts/
pole_assessments/
figures/
figures/site_level_examples/
.github/workflows/
```

GitHub does not create empty folders directly. To create a folder in the browser:

1. Click `Add file` → `Create new file`.
2. In the file name box, type for example:

`data/.gitkeep`

3. Commit the file.

Repeat the same idea for:

```text
pages/.gitkeep
scripts/.gitkeep
pole_assessments/.gitkeep
figures/site_level_examples/.gitkeep
.github/workflows/.gitkeep
```

The `.gitkeep` files are only placeholders.

---

## 3. Create the homepage

Create this file in the root of the repository:

`index.html`

A simple starting version is:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Baltica Precambrian Poles</title>
</head>
<body>
  <h1>Baltica Precambrian Poles</h1>
  <p>Working database prototype for Baltica Precambrian poles.</p>

  <ul>
    <li><a href="pages/pole_compilation.html">Pole compilation</a></li>
    <li><a href="pages/interactive_pole_map.html">Interactive pole map</a></li>
    <li><a href="pages/paleolatitude.html">Baltica paleolatitude through time</a></li>
    <li><a href="pole_assessments/">Pole assessments</a></li>
  </ul>
</body>
</html>
```

Later this can be replaced by a better designed homepage.

---

## 4. Create placeholder pages

Create these files inside the `pages/` folder:

```text
pages/pole_compilation.html
pages/interactive_pole_map.html
pages/paleolatitude.html
pages/revisions_and_additions.html
pages/resources.html
```

At the start, these pages can be simple placeholders. For example:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Pole compilation</title>
</head>
<body>
  <h1>Pole compilation</h1>
  <p>This page will be generated from data/Baltica_poles.csv.</p>
</body>
</html>
```

The rebuild scripts will later replace some of these placeholder pages.

---

## 5. Add the main pole compilation file

Upload the main pole file to:

`data/Baltica_poles.csv`

The filename must be exactly:

`Baltica_poles.csv`

Recommended column structure:

```text
Terrane;Unit;Age_Ma;age_min;age_max;Rating;S_LONG;S_LAT;P_LONG;P_LAT;A95;Reference
```

Column meanings:

| Column | Meaning |
|---|---|
| `Terrane` | Baltica terrane or region |
| `Unit` | pole/unit name shown on the webpage |
| `Age_Ma` | nominal age in Ma |
| `age_min` | younger/lower age bound |
| `age_max` | older/upper age bound |
| `Rating` | reliability grade, for example A, B, C+, C |
| `S_LONG` | present-day sampling longitude |
| `S_LAT` | present-day sampling latitude |
| `P_LONG` | paleomagnetic pole longitude |
| `P_LAT` | paleomagnetic pole latitude |
| `A95` | pole A95 confidence cone |
| `Reference` | source reference |

Important rules:

- Keep the file semicolon-separated.
- Keep the exact column names.
- Use `P_LONG` and `P_LAT`, not `PLONG` and `PLAT`.
- Coordinates must be single numeric values.
- Do not use ranges such as `21--27` in `S_LONG` or `S_LAT`.

---

## 6. Add the site-level workbook

Upload the site-level workbook to:

`data/site_level_data_site_comments_added.xlsx`

Each sheet should represent one pole/unit.

Recommended columns in each sheet:

```text
site | dir_dec | dir_inc | dir_k | dir_alpha95 | dir_n_samples | vgp_lat | vgp_lon | authors | comment
```

Column meanings:

| Column | Meaning |
|---|---|
| `site` | site or site-mean label |
| `dir_dec` | declination |
| `dir_inc` | inclination |
| `dir_k` | Fisher precision |
| `dir_alpha95` | site alpha95 |
| `dir_n_samples` | number of samples/specimens |
| `vgp_lat` | VGP latitude |
| `vgp_lon` | VGP longitude |
| `authors` | source reference |
| `comment` | accepted/rejected/digitized/inverted/uncertain notes |

Rules:

- Use one sheet per pole/unit.
- Do not use merged cells.
- Keep numerical columns numerical.
- Keep sheet names stable.

---

## 7. Add the pole-to-sheet matching file

Create/upload:

`data/pole_sheet_match.csv`

This file links each pole page to the correct sheet in the site-level Excel workbook.

Recommended columns:

```text
master_row,pole_id,unit,age_ma,rating,reference,matched_sheet,sheet_rows,match_status,note
```

Important fields:

- `pole_id`: internal page identifier.
- `unit`: pole/unit name.
- `matched_sheet`: Excel sheet name.
- `sheet_rows`: number of rows in the sheet.
- `match_status`: exact, strong, manual, uncertain, missing, exact_empty.
- `note`: explanation of problems or manual choices.

---

## 8. Add the scientific assessment text file

Create/upload:

`data/pole_assessment_notes_template.csv`

This file contains written scientific assessment text for the pole pages.

Recommended sections:

1. Geological context
2. Magnetization components
3. Age constraints
4. Site-level data
5. Paleosecular variation
6. Comparison to Baltica A-/B-grade poles
7. Comparison to younger Baltica poles
8. Notes/status

Long scientific interpretation should go here, not in the Excel workbook.

---

## 9. Add Python requirements

Create this file in the root:

`requirements.txt`

A typical version is:

```text
pandas
openpyxl
matplotlib
numpy
folium
branca
cartopy
```

GitHub Actions uses this file to install the required Python packages.

---

## 10. Add the Python scripts

Upload the generation scripts into the `scripts/` folder:

```text
scripts/build_interactive_pole_map.py
scripts/build_pole_compilation_page.py
scripts/make_site_level_example_plots.py
scripts/rebuild_pole_assessment_pages.py
```

Their roles are:

- `build_interactive_pole_map.py`: creates `pages/interactive_pole_map.html`.
- `build_pole_compilation_page.py`: creates `pages/pole_compilation.html`.
- `make_site_level_example_plots.py`: creates PNG site-level figures.
- `rebuild_pole_assessment_pages.py`: creates/updates pole assessment pages.

---

## 11. Create the GitHub Actions workflow

Create this file:

`.github/workflows/rebuild_site.yml`

Use this content:

```yaml
name: Rebuild Baltica figures

on:
  workflow_dispatch:
  push:
    paths:
      - "data/**"
      - "scripts/**"
      - "requirements.txt"
      - ".github/workflows/rebuild_site.yml"

permissions:
  contents: write

jobs:
  rebuild:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Build interactive pole map
        run: |
          python scripts/build_interactive_pole_map.py

      - name: Build pole compilation page
        run: |
          python scripts/build_pole_compilation_page.py

      - name: Generate site-level example plots
        run: |
          python scripts/make_site_level_example_plots.py

      - name: Rebuild pole assessment site-level tables
        run: |
          python scripts/rebuild_pole_assessment_pages.py

      - name: Commit generated outputs
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git pull --rebase --autostash origin main
          git add figures/ pole_assessments/ pages/
          if git diff --cached --quiet; then
            echo "No generated changes to commit"
          else
            git commit -m "Auto rebuild Baltica figures, maps, and pages"
            git push
          fi
```

Important: YAML indentation must not be changed randomly. Every `- name:` step must align with the other steps.

---

## 12. Enable GitHub Pages

1. Open the GitHub repository.
2. Click `Settings`.
3. Click `Pages`.
4. Under `Build and deployment`, choose `Deploy from a branch`.
5. Branch: `main`.
6. Folder: `/root`.
7. Click `Save`.

After a short time, the public webpage will be available.

For this repository:

`https://ahmedpaleomag.github.io/Baltica_Precambrian_Poles/`

For another repository:

`https://USERNAME.github.io/REPOSITORY_NAME/`

---

## 13. Run the first rebuild

1. Go to `Actions`.
2. Select `Rebuild Baltica figures`.
3. Click `Run workflow`.
4. Select branch `main`.
5. Click `Run workflow`.
6. Wait until the workflow is green.

The workflow should generate:

- the pole compilation page,
- the interactive pole map,
- pole assessment pages,
- site-level figures.

---

## 14. Check the public webpage

Open:

`https://ahmedpaleomag.github.io/Baltica_Precambrian_Poles/`

Check:

```text
pages/pole_compilation.html
pages/interactive_pole_map.html
pole_assessments/
```

If the browser shows an old version, press:

`Ctrl + F5`

or add a temporary suffix:

`?v=20260707`

Example:

`https://ahmedpaleomag.github.io/Baltica_Precambrian_Poles/pages/pole_compilation.html?v=20260707`

---

# PART 2 — UPDATE AN EXISTING WEBPAGE

## 15. Normal update workflow

For routine updates:

```text
1. Edit source files in data/
2. Upload/commit them to GitHub
3. Run Actions → Rebuild Baltica figures
4. Wait for green workflow
5. Check the public webpage
```

---

## 16. Updating the pole compilation

Edit:

`data/Baltica_poles.csv`

Then upload/replace it with the same filename.

Run:

`Actions → Rebuild Baltica figures`

This updates:

- `pages/pole_compilation.html`,
- `pages/interactive_pole_map.html`.

---

## 17. Updating site-level data

Edit:

`data/site_level_data_site_comments_added.xlsx`

If sheet names changed, also edit:

`data/pole_sheet_match.csv`

Then run the rebuild workflow.

---

## 18. Updating scientific text

Edit:

`data/pole_assessment_notes_template.csv`

Then run the rebuild workflow.

---

## 19. Adding a new pole later

1. Add the pole to `data/Baltica_poles.csv`.
2. Add a site-level sheet if available.
3. Link it in `data/pole_sheet_match.csv`.
4. Add scientific assessment text.
5. Run the rebuild workflow.
6. Check pole compilation, map, and pole assessment page.

---

## 20. Troubleshooting

### Pole compilation shows old number of poles

Check:

- The file is named exactly `data/Baltica_poles.csv`.
- The workflow finished green.
- `pages/pole_compilation.html` was committed.
- The browser is not showing a cached page.

### Interactive map fails

Check:

- `S_LONG` and `S_LAT` are numeric.
- `P_LONG` and `P_LAT` are numeric.
- No coordinate cell contains a range such as `21--27`.
- Column names are correct.

### Site-level table is missing

Check:

- The sheet exists in the Excel workbook.
- The sheet name matches `pole_sheet_match.csv`.
- Required columns are present.
- Workflow finished green.

### VGP/PSV figures are missing

Check:

- `dir_dec` and `dir_inc` are numeric.
- `vgp_lat` and `vgp_lon` are numeric.
- The pole is correctly linked to the sheet.
- There are enough valid rows.

---

## 21. Key rule

The safe workflow is:

```text
Create/edit source data → commit to GitHub → run rebuild workflow → check public webpage
```

Avoid editing generated HTML manually unless it is a temporary emergency correction.
