from validation_common import fail, read_csv, ROOT

import zipfile

errors = []
rows = read_csv(ROOT / "manifests/PACKAGE_PLAN.csv")
if len(rows) != 4:
    errors.append("expected exactly 4 package plans")
package_dir = ROOT / "deliverables" / "packages"
zips = {p.name: p for p in package_dir.glob("*.zip")} if package_dir.is_dir() else {}
for r in rows:
    count = int(r["estimated_file_count"])
    if count > 100:
        errors.append(f"{r['package_id']}: estimated files exceed 100")
    if r["flattened"] != "YES":
        errors.append(f"{r['package_id']}: upload package is not planned flat")
    if r["status"] != "final":
        errors.append(f"{r['package_id']}: unexpected status")
    matches = [name for name in zips if name.startswith(r["package_id"])]
    if len(matches) != 1:
        errors.append(f"{r['package_id']}: expected exactly one ZIP in deliverables/packages, found {len(matches)}")
        continue
    with zipfile.ZipFile(zips[matches[0]]) as zf:
        infos = zf.infolist()
        if len(infos) != count:
            errors.append(f"{r['package_id']}: ZIP holds {len(infos)} files, plan says {count}")
        for info in infos:
            if "/" in info.filename or "\\" in info.filename:
                errors.append(f"{r['package_id']}: entry {info.filename} is not flat")
            if info.filename.startswith("#U"):
                errors.append(f"{r['package_id']}: escaped filename {info.filename}")
fail(errors)
print("PASS: 4 final packages are <=100 files, root-flat and match their ZIPs")
