# Data sources

## `skpg_2024_first_degree_income_by_field.csv` (real, published)

Transcribed by hand from **Jadual 4o, "Pendapatan Bulanan Graduan 2024 bagi Peringkat
Ijazah Pertama, Diploma dan Sijil Mengikut Bidang Pengajian"**, page 64 of:

> Kementerian Pendidikan Tinggi (2025). *Laporan Kajian Pengesanan Graduan 2024*.
> Putrajaya. ISSN 2756-7907.
> https://mohe.gov.my/en/download/publications-journals-and-reports/lkpg/2024-5/1740-laporan-skpg-tahun-2024-pdf/file

Only the first-degree (Ijazah Pertama) rows are used. Each row gives the number of
employed respondents in a field of study and the percentage of them in each of nine
monthly income bands. The report's own note applies: graduates working for family
without pay are excluded.

The report's overall first-degree row (n = 109,414) is: 6.9, 6.2, 17.5, 19.1, 16.6, 22.7,
6.6, 3.8, 0.6 per cent. The field rows sum to that total, which `tests/` checks.

The `stem` column is **not** from the report. It is this project's classification:
engineering, ICT, and natural sciences/mathematics/statistics are coded 1 (ISCED-F broad
fields 05, 06 and 07). Health and agriculture are coded 0. Other definitions of STEM
include them; changing the column changes the STEM coefficient.

## Policy parameters (real, announced)

Budget 2027, tabled 9 October 2026: the national minimum wage rises from RM1,700 to
RM2,000 from June 2027, and a RM2,500 monthly floor for semi-skilled workers and
graduates is introduced "as a starting point". No start date was given for the RM2,500
floor, and SMEs with sales under RM50 million are exempt from the new minimum wage.

- https://berita.rtm.gov.my/nasional/senarai-berita-nasional/senarai-artikel/gaji-minimum-naik-rm2000-mulai-jun-2027/
- https://www.malaysiakini.com/news/886673-gaji-minimum-rm2000-had-pelepasan-cukai-individu-naik-ke-rm12000

## Statutory contribution rates (real, simplified)

EPF 13% employer / 11% employee (wages of RM5,000 and below), SOCSO 1.75% / 0.5%,
EIS 0.2% / 0.2%, HRD Corp levy 1%. SOCSO and EIS are really set by contribution tables
with a wage ceiling, so the flat percentages are an approximation. Income tax (PCB) is
not modelled.

## Everything else (assumed)

SKPG does not publish CGPA, internship length or work location alongside income. Those
three variables, and how strongly each relates to salary, are **assumptions** set in
`config/parameters.json` under `simulation`. See the README for what that means for
interpreting the regression.
