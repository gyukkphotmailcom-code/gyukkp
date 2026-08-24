#!/usr/bin/env python3
"""Validate dimensions, palette, alpha, metadata, hashes and reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
MANIFEST = HERE / "concept_action_p0_manifest.json"
BUILDER = HERE / "build_concept_action_p0.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(manifest):
    paths = [HERE / f["file"] for f in manifest["frames"]]
    paths += [HERE / manifest["boards"]["derivedSpriteReview"]["file"], HERE / manifest["boards"]["actionSkeleton"]["file"]]
    return {str(p.relative_to(HERE)): sha256(p) for p in paths}


def validate_once():
    errors = []
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    allowed = {tuple(c) for c in m["palette"]["rgba"]}
    expected_canvas = {"SURF0": (160,128), "JUMP_AIR": (128,128), "UW_NORMAL": (160,128)}
    required_fields = {
        "sourceFrame","movementVector","bodyAxis","bodyYawToCamera","headYawToCamera",
        "nearFarLimbOrder","waterlineOrDepthPlane","root","visibleBBox","palette","sha256",
    }
    if len(m.get("frames",[])) != 6:
        errors.append("manifest must contain exactly 6 frames")
    for f in m.get("frames",[]):
        missing = required_fields - set(f)
        if missing: errors.append(f"{f.get('id')}: missing fields {sorted(missing)}")
        path = HERE / f["file"]
        if not path.exists():
            errors.append(f"{f['id']}: missing PNG"); continue
        if sha256(path) != f["sha256"]: errors.append(f"{f['id']}: sha256 mismatch")
        with Image.open(path) as im:
            if im.mode != "RGBA": errors.append(f"{f['id']}: mode {im.mode}, expected RGBA")
            if im.size != expected_canvas[f["pose"]]: errors.append(f"{f['id']}: canvas {im.size}")
            alphas = set(im.getchannel("A").getdata())
            if not alphas <= {0,255}: errors.append(f"{f['id']}: alpha values {sorted(alphas)}")
            colors = {px for px in im.getdata() if px[3]}
            extra = colors - allowed
            if extra: errors.append(f"{f['id']}: {len(extra)} colors outside fixed palette")
            bbox = im.getchannel("A").getbbox()
            inclusive = None if bbox is None else [bbox[0],bbox[1],bbox[2]-1,bbox[3]-1]
            if inclusive != f["visibleBBox"]: errors.append(f"{f['id']}: visibleBBox mismatch")
            required_meta = {"stage","pose","character","identityLock","sourceFrame","orientation","reviewState"}
            miss_meta = required_meta - set(im.info)
            if miss_meta: errors.append(f"{f['id']}: missing PNG metadata {sorted(miss_meta)}")
            if im.info.get("pose") != f["pose"] or im.info.get("character") != f["character"]:
                errors.append(f"{f['id']}: PNG metadata identity mismatch")
    for key in ("derivedSpriteReview","actionSkeleton"):
        p = HERE / m["boards"][key]["file"]
        if not p.exists() or sha256(p) != m["boards"][key]["sha256"]: errors.append(f"{key}: hash mismatch")
    html = ROOT / m["formalGame"]["file"]
    actual = sha256(html)
    if actual != m["formalGame"]["expectedSha256"]:
        errors.append(f"formal HTML hash changed: {actual}")
    ignored = subprocess.run(["git","check-ignore","-q",str(HERE/"本地勿提交/FC与概念模型对照板-本地勿提交.png")], cwd=ROOT).returncode == 0
    if not ignored: errors.append("private comparison board is not git-ignored")
    return m, errors


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rebuild",action="store_true"); args=ap.parse_args()
    before_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    before = snapshot(before_manifest)
    if args.rebuild:
        subprocess.run([sys.executable,str(BUILDER)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        after_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        after = snapshot(after_manifest)
        if before != after:
            print("FAIL reproducibility: output hashes changed",file=sys.stderr)
            print(json.dumps({"before":before,"after":after},ensure_ascii=False,indent=2),file=sys.stderr)
            return 1
    m,errors=validate_once()
    if errors:
        print("FAIL")
        for e in errors: print("-",e)
        return 1
    print("PASS CONCEPT-ACTION-0-P0")
    print("frames=6 alpha={0,255} palette=fixed metadata=complete hashes=match")
    print("formalHTML="+m["formalGame"]["actualSha256"])
    print("reproducible="+("yes" if args.rebuild else "not-run"))
    print("visualApproval=pending-user-review")
    return 0


if __name__=="__main__": raise SystemExit(main())
