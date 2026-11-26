<!-- Implements: package/dashboard-guide -->
# Dashboard guide: the KPI model in Data Studio

This guide builds a one-page dashboard on the KPI workbook in Google's free dashboard tool. Google renamed Looker
Studio to Data Studio in April 2026; it connects to a Google Sheets worksheet directly, and its paid tier is a
separate product [src:data-studio-sheets-free]. Every figure on the dashboard is simulated, so the page says so
in its title. Allow about 30 minutes.

## 1. Connect the data

1. Upload `deliverables/kpi-model.xlsx` to Google Drive and open it with Google Sheets (File → Save as Google Sheets).
2. Open datastudio.google.com (the old lookerstudio.google.com address redirects) and create a blank report.
3. Add data → Google Sheets → the workbook → worksheet **Looker data**.
4. Keep "Use first row as headers" ticked and set **Optional range** to `A2:E`. Row 1 of every tab is the
   "simulated" banner, so the headers start in row 2.
5. Check the fields: `Case` (text), `Process` (text), `Case type` (text), `KPI` (text), `Value` (number).

## 2. Page setup

- Title text box: "AI-first onboarding and KYC review: KPI model (simulated data)".
- Under it, a text box: "Simulated cases walked through the As-Is and To-Be maps. Every input is a labelled guess
  on the workbook's Assumptions tab. Not real bank data."
- Add a **drop-down list control** on `Case type`, single-select, with its **default selection** set to
  `onboarding`. Without a default it shows all values, and charts 1–4 would average onboarding and review cases
  together, a figure that matches nothing in the deck.

## 3. Charts

### Chart 1: Cycle time, As-Is vs To-Be

- Type: column chart. Dimension: `Process`. Metric: `Value` with aggregation **Average**.
- Filter: KPI = `Cycle time (days)`.
- Style: show data labels; colour As-Is orange and To-Be blue (the same colours as the deck's charts).

### Chart 2: Touch time per case

- As chart 1, with filter KPI = `Touch time (hours)`.

### Chart 3: First-pass rate

- As chart 1, with filter KPI = `First pass (1 = yes)`. The average of a 1/0 field is the share. To show it as a
  percentage, set the metric's data type to Numeric → Percent; the "Percent" display format alone treats 0.87 as
  0.87% and shows 1%.

### Chart 4: Client touches

- As chart 1, with filter KPI = `Client touches`.

### Chart 5: Reviews on time

- As chart 3, with filter KPI = `On time (1 = yes)`. Only reviews have this KPI, so the case-type control shows it
  for reviews alone.

### Chart 6: Distribution of cycle time

- Type: table with heatmap. Dimensions: `Process`, then `Case` (case IDs repeat across As-Is and To-Be, so
  `Process` must come first or the two would be added together). Metric: `Value` with aggregation **Average**
  (one row per case, so this is the case's own cycle time). Filter KPI = `Cycle time (days)`; sort by `Value`
  descending. It shows the long tail that averages hide.

## 4. Share

Share → Manage access → "Anyone with the link can view". For the site, use File → Embed report and copy the
embed URL (a plain report link may show only as a link card). The Sheets connector took the open-ended range
`A2:E` when this was built; if it ever refuses, use `A2:E20000`.
