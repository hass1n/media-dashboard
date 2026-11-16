import openpyxl
import os

# ============================================================
# 1. Excel file path
# ============================================================

file_path = r"C:\Users\lenovo\Downloads\FAQ_updated.xlsx"


# ============================================================
# 2. Mapping: Category / main issue -> Big Category
# ============================================================

category_mapping = {
    "عدم الثقة بالهيئة الناظمة":
        "فقدان الثقة بالإصلاحات والجهات المسؤولة",

    "الفساد والمحاسبة":
        "الفساد والمحاسبة والهدر",

    "الفساد والهدر":
        "الفساد والمحاسبة والهدر",

    "أصحاب المولدات":
        "قطاع المولدات والتعرفة والجباية",

    "هدر المال العام":
        "الفساد والمحاسبة والهدر",

    "التعرفة والجباية":
        "قطاع المولدات والتعرفة والجباية",

    "الفساد والمحاصصة":
        "الفساد والمحاسبة والهدر",

    "فقدان الثقة والاستثمار":
        "فقدان الثقة بالإصلاحات والجهات المسؤولة",

    "فقدان الثقة":
        "فقدان الثقة بالإصلاحات والجهات المسؤولة",

    "التشكيك بالإصلاحات":
        "فقدان الثقة بالإصلاحات والجهات المسؤولة",

    "عدم الثقة بالوعود":
        "فقدان الثقة بالإصلاحات والجهات المسؤولة",

    "حلول سريعة للكهرباء":
        "الحلول والإصلاحات في قطاع الكهرباء",

    "انتقاد مباشر":
        "انتقاد عام لقطاع الكهرباء",
}


# ============================================================
# 3. Open the existing Excel file
# ============================================================

wb = openpyxl.load_workbook(file_path)


# ============================================================
# 4. Select the electricity sheet
# ============================================================

# This works whether the sheet is named "electricity" or "Electricity"
sheet_name = None

for sheet in wb.sheetnames:
    if sheet.strip().lower() == "electricity":
        sheet_name = sheet
        break

if sheet_name is None:
    raise ValueError(
        f"Electricity sheet not found. Available sheets: {wb.sheetnames}"
    )

ws = wb[sheet_name]


# ============================================================
# 5. Find "Category / main issue" column
# ============================================================

header_row = 1
category_col = None

for cell in ws[header_row]:

    if (
        cell.value is not None
        and str(cell.value).strip() == "Category / main issue"
    ):
        category_col = cell.column
        break


if category_col is None:
    raise ValueError(
        '"Category / main issue" column was not found.'
    )


# ============================================================
# 6. Add "Big Category" beside it
# ============================================================

big_category_col = category_col + 1

ws.insert_cols(big_category_col)

ws.cell(
    row=header_row,
    column=big_category_col
).value = "Big Category"


# ============================================================
# 7. Fill Big Category for every row
# ============================================================

filled_rows = 0
unmatched_categories = []


for row in range(header_row + 1, ws.max_row + 1):

    value = ws.cell(
        row=row,
        column=category_col
    ).value

    # Skip empty cells
    if value is None:
        continue

    category = str(value).strip()

    if category == "":
        continue


    # Check if category exists in our mapping
    if category in category_mapping:

        ws.cell(
            row=row,
            column=big_category_col
        ).value = category_mapping[category]

        filled_rows += 1

    else:

        unmatched_categories.append(
            (row, category)
        )


# ============================================================
# 8. Save back to the SAME Excel file
# ============================================================

wb.save(file_path)


# ============================================================
# 9. Print results
# ============================================================

print("======================================")
print("Done!")
print("======================================")

print(f"File updated: {file_path}")
print(f"Sheet: {sheet_name}")
print(f"Rows filled: {filled_rows}")


if unmatched_categories:

    print("\nCategories not found in the mapping:")

    for row, category in unmatched_categories:
        print(
            f"Row {row}: {category}"
        )

else:

    print(
        "\nAll categories were successfully mapped."
    )