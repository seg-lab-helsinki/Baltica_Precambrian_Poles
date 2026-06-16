# Baltica Precambrian Pole Compilation — v6 assessment scaffold

Working GitHub Pages prototype for the Baltica Precambrian paleomagnetic pole compilation.

Live page:
https://ahmedpaleomag.github.io/Baltica_Precambrian_Poles/

## Current source/input files

- `data/Baltica_poles.csv` — master pole compilation.
- `data/site_level_data_site_comments_added.xlsx` — current living site-level workbook.
- `data/pole_sheet_match.csv` — matching table linking each master pole to the correct Excel sheet.
- `data/pole_assessment_notes_template.csv` — placeholder table for scientific assessment text.
- `data/vgp_attention_tracker.csv` — tracker for VGP/site-level files that need attention.

## Generated output files

- `index.html` — searchable/filterable compilation table.
- `pole_assessments/*.html` — generated pole assessment pages.

## Current page structure

Each pole page includes:

1. Pole metadata
2. Site-level link status
3. Scientific assessment scaffold:
   - Geological context
   - Magnetization components
   - Age constraints
   - Site-level data
   - PSV variation
   - Comparison to Baltica A-/B-grade poles
   - Comparison to younger Baltica poles
4. Current site-level data table from the linked Excel sheet

## Update rule

Treat the website as a living database. Update the source files first, then regenerate the HTML pages. Do not manually edit scientific content directly in the generated HTML.
