from validation_common import fail, read_csv, ROOT

errors = []
rows = read_csv(ROOT / "manifests/PACKAGE_PLAN.csv")
if len(rows) != 3: errors.append("expected exactly 3 package plans")
for r in rows:
    if int(r["estimated_file_count"]) > 100: errors.append(f"{r['package_id']}: estimated files exceed 100")
    if r["flattened"] != "YES": errors.append(f"{r['package_id']}: upload package is not planned flat")
    if r["status"] != "planned": errors.append(f"{r['package_id']}: unexpected status")
if list((ROOT / "deliverables").glob("*.zip")):
    print("NOTE: ZIP files found; inspect them in Stage 6")
else:
    print("PASS: no final ZIP created in Stage 1.1")
fail(errors)
print("PASS: all planned packages are <=100 files and root-flat")
