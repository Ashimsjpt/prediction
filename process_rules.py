import pdfplumber
import pandas as pd

PDF_PATH = "data/raw/2026 Trout Stocking Frequencies 050726.pdf"

records = []

Frequency_rules = {
1: "weekly before July 31, then twice before laborday, once in fall",
2: "twice each month from april through labour day",
3: "once each month form march thru august",
4: "four times from amrch through august",
5: "twice each year in march and may",
6: "once each year"
}

Modifier_rules = {
    (1, "*"): "stop after july 4",
    (1, "**"): "twice monthly after july 4",
    (2, "*"): "stop after july 4",
    (2, "**"): "once monthly after july 4",
    (2, "***"): "under construction ; once monthly in fall/winter when complete",
    (4, "*"): "stop after july 4"
}

with pdfplumber.open(PDF_PATH) as pdf:
    table_number = 1
    
    for page_number, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables() 

        for table in tables:
            for row in table[1:]:
                if not row:
                    continue

                if row[0] and row[1]:
                    records.append({
                        "waterbody" : row[0],
                        "county": row[1],
                        "table": table_number
                    })

                if len(row) >= 4 and row[2] and row[3]:
                     records.append({
                        "waterbody" : row[2],
                        "county": row[3],
                        "table": table_number
                    })

            table_number +=1
df_rules = pd.DataFrame(records)


df_rules["modifier"] = df_rules["waterbody"].str.extract(r"(\*+)$")

df_rules["waterbody"]=(
    df_rules["waterbody"]
    .str.replace(r"\*+$", "", regex= True)
    .str.strip()
)

print(df_rules.head(20))
print("row:", len(df_rules))
