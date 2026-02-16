from pathlib import Path

p = Path("run_local_portal.py")
lines = p.read_text(encoding="utf-8").splitlines(True)

route1 = "@app.route('/admin/payment/<int:payment_id>/delete', methods=['POST'])"
route2 = '@app.route("/admin/payment/<int:payment_id>/delete", methods=["POST"])'

# Find all occurrences
idxs = [i for i, ln in enumerate(lines) if route1 in ln or route2 in ln]
print("Found route occurrences:", idxs)

if len(idxs) <= 1:
    print("✅ No duplicate route found. Nothing to remove.")
    raise SystemExit(0)

# Keep the FIRST occurrence, remove subsequent blocks
keep = idxs[0]
remove_starts = idxs[1:]

to_remove = set()

for start in remove_starts:
    # remove from decorator line until after the function block
    # heuristic: remove until we hit the next route decorator or end of file
    i = start
    while i < len(lines):
        to_remove.add(i)
        i += 1
        if i < len(lines):
            nxt = lines[i]
            if nxt.lstrip().startswith("@app.route(") or nxt.startswith("if __name__"):
                break

out = [ln for i, ln in enumerate(lines) if i not in to_remove]
p.write_text("".join(out), encoding="utf-8")
print(f"✅ Removed {len(remove_starts)} duplicate route block(s).")
