#!/usr/bin/env python3
"""阶段3A R3A：原版人体母版（不含阳阳/爸爸身份层）。

目标只有一个：先得到在原生 1× 下像完整人物、且内部像素可追溯到原版
参考裁剪的人体母版。此脚本不读取 avatar_paint.py，不生成阳阳/爸爸，不修改
主 HTML，也不复用 R2 的手写 BASE_SEGS / IDENTITY_RUNS。

流程：
  锁定参考裁剪 + 显式 clean subject mask + 固定调色分类器
      -> canonical L 原版人体母版 -> 严格水平镜像 R

用法：
  python3 build_sprites_r3a.py --make-subjects
  python3 build_sprites_r3a.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
REF_DIR = BASE / "阶段3A0参考"

OUT_JS = BASE / "sprites_r3a_human_baked.js"
OUT_AUDIT = BASE / "阶段3A-R3A人体母版审核表.png"
OUT_BLIND = BASE / "阶段3A-R3A人体盲审图.png"

POSES = ("SURF0", "JUMP_AIR", "UW_NORMAL")
CLASSIFIER_ID = "original-human-nearest-semantic"
CLASSIFIER_VERSION = 1


SURFACE_RGB = {
    "O": (0, 0, 0),
    "D": (60, 32, 24),
    "d": (120, 64, 49),
    "s": (180, 96, 73),
    "S": (241, 129, 98),
    "W": (241, 242, 241),
}
UW_RGB = {
    "O": (0, 64, 88),
    "M": (60, 188, 252),
    "L": (164, 228, 252),
    "W": (252, 252, 252),
}
UW_CHAR = {"O": "u", "M": "m", "L": "l", "W": "w"}
RENDER_RGB = {**SURFACE_RGB, **{UW_CHAR[k]: v for k, v in UW_RGB.items()}}


POSE_SPEC = {
    "SURF0": {
        "cn": "水面俯泳",
        "w": 31,
        "h": 21,
        "source": "surf0_mask_source.png",
        "source_sha256": "e7665833b0f755785faab35442225789a0d3b0ba8b0995c7d0c4b416a07afa4c",
        "legacy_mask": "mask_SURF0.png",
        "legacy_mask_sha256": "f9c509b6e481b5f345e8b3463fc41851c9551ce3c1ee6c80a14e8a3b1512279f",
        "legacy_json": "mask_SURF0.json",
        "legacy_json_sha256": "eefec93ddcf89a95186a24c55833d1c965353323e31dae8a9e187acba2f2e51e",
        "provenance": {
            "sourceFile": "原版参考/官方截图/jp-action-e.gif",
            "sourceSha256": "698d51036ec2fc82ac1c40fa4cdcd784dda5192bca95a7b378d575f449712f72",
            "sourceOriginalSize": [256, 192], "frameIndex": None, "frameBase": 0, "fps": None,
            "maskCropBox": [105, 88, 136, 109], "referenceCropFile": "surf0_mask_source.png",
            "referenceCropSha256": "e7665833b0f755785faab35442225789a0d3b0ba8b0995c7d0c4b416a07afa4c",
        },
        "subject": "subject_R3A_SURF0.png",
        "subject_json": "subject_R3A_SURF0.json",
        "source_version": "日版官方宣传图 jp-action-e.gif 原生裁剪",
        "source_facing": "TBD（单帧姿态方向命名待独立原版证据确认）",
        "root_l": (15, 10),
        "root_desc": "surfaceContactRoot（不是物理质心）",
        "review_head_roi": (0, 0, 21, 11),
        "evidence_limit": "静态宣传图；证明可见人物像素，不证明动画时序或ROM原生色",
    },
    "JUMP_AIR": {
        "cn": "空中飞扑",
        "w": 55,
        "h": 42,
        "source": "jump_mask_source.png",
        "source_sha256": "8ac663c4c78846ce8f20825517aca38d01573c0e24d9f62bbb6ad7d95f55b81a",
        "legacy_mask": "mask_JUMP_AIR.png",
        "legacy_mask_sha256": "a8664813fdc9c32f4a7fd87618b99b679667caaf605ba8e552a66ab8cc939409",
        "legacy_json": "mask_JUMP_AIR.json",
        "legacy_json_sha256": "59083dc9669bd6c23901036e9a498bc505b54f9997ff24c2c1116dfc0d9efaba",
        "provenance": {
            "sourceFile": "原版参考/官方截图/jp-action-c.gif",
            "sourceSha256": "75c2d446adaaa15a46e9bc8bcaf47a483dfb2502095dc581ed68e9b6680ba077",
            "sourceOriginalSize": [256, 192], "frameIndex": None, "frameBase": 0, "fps": None,
            "maskCropBox": [73, 35, 128, 77], "referenceCropFile": "jump_mask_source.png",
            "referenceCropSha256": "8ac663c4c78846ce8f20825517aca38d01573c0e24d9f62bbb6ad7d95f55b81a",
        },
        "subject": "subject_R3A_JUMP_AIR.png",
        "subject_json": "subject_R3A_JUMP_AIR.json",
        "source_version": "日版官方宣传图 jp-action-c.gif 原生裁剪",
        "source_facing": "L（R仅为镜像候选）",
        "root_l": (22, 41),
        "root_desc": "脚底中心",
        "review_head_roi": (11, 0, 35, 12),
        "evidence_limit": "静态宣传图；证明飞扑可见姿态，不证明起跳/下落时序",
    },
    "UW_NORMAL": {
        "cn": "水下横泳",
        "w": 39,
        "h": 21,
        "source": "uw_official_b_source_R.png",
        "source_sha256": "88f085a4a6d3bd59b30d23bd4fb173dfe541abb99ed4b40304f0dbf76574ded8",
        "legacy_mask": "mask_UW_OFFICIAL_B_R.png",
        "legacy_mask_sha256": "a67aefa4fca9b202376d605017514d025debac9f41ed92927d1c9bc6a77ad56e",
        "legacy_json": "mask_UW_OFFICIAL_B_R.json",
        "legacy_json_sha256": "665ac4cb18a6780d8b699592fb62242d0c58cc3036ea55c7885ad1b3a47d1363",
        "provenance": {
            "sourceFile": "原版参考/官方截图/jp-action-b.gif",
            "sourceSha256": "80e1a0321324d56f594c2ef851946629915a90d7060d5309c3c5de664cf15c57",
            "sourceOriginalSize": [256, 192], "frameIndex": None, "frameBase": 0, "fps": None,
            "maskCropBox": [99, 141, 138, 162],
            "sourceFacing": "R-candidate (static front-biased; exact movement direction TBD)",
            "normalizedFacing": "L-candidate", "transform": "horizontal_flip",
            "referenceCropFile": "uw_official_b_source_R.png",
            "referenceCropSha256": "88f085a4a6d3bd59b30d23bd4fb173dfe541abb99ed4b40304f0dbf76574ded8",
            "recipeId": "official-b-rgt5-components-row-spans-v1",
            "recipeVersion": 1,
            "pixels": 425,
        },
        "subject": "subject_R3A_UW_NORMAL.png",
        "subject_json": "subject_R3A_UW_NORMAL.json",
        "source_version": "日版官方宣传图 jp-action-b.gif 水下单人；R源镜像为canonical L",
        "source_facing": "canonical L候选（静态图偏正面；R移动方向未独立证明）",
        "normalize_transform": "horizontal_flip",
        "root_l": (20, 11),
        "root_desc": "可见alpha几何中心候选（非物理/碰撞锚）",
        "review_head_roi": (10, 1, 25, 15),
        "evidence_limit": "日版静态宣传图；证明可见人体姿态/调色，不证明动画时序或ROM CHR来源",
    },
}


# SURF 不再从颜色阈值、白吸附和 fill_holes 推断；这是逐像素复核后的显式可见人体。
# run 为闭区间 (x0, x1)。
SURF0_CLEAN_RUNS = {
    0: [(2, 18)], 1: [(2, 18)], 2: [(0, 19)], 3: [(0, 19)],
    4: [(0, 19)], 5: [(0, 19)], 6: [(0, 19)], 7: [(0, 19)],
    8: [(2, 2), (5, 19)], 9: [(5, 19)], 10: [(2, 20)],
    11: [(1, 24)], 12: [(2, 26)], 13: [(3, 26)],
    14: [(3, 29)], 15: [(3, 29)], 16: [(2, 29)],
    17: [(1, 29)], 18: [(0, 30)], 19: [(2, 26)], 20: [(3, 15)],
}

# JUMP同样用逐行复核后的最终可见人体，不在构建时做“矩形补肢体”。
JUMP_CLEAN_RUNS = {
    0: [(13, 33), (36, 43)], 1: [(11, 44)], 2: [(11, 45)], 3: [(11, 46)],
    4: [(11, 47)], 5: [(11, 48)], 6: [(11, 48)], 7: [(11, 46)],
    8: [(11, 46)], 9: [(11, 44)], 10: [(11, 31), (34, 42)],
    11: [(11, 31), (34, 41)], 12: [(10, 40)], 13: [(9, 39)],
    14: [(4, 38)], 15: [(2, 38)], 16: [(1, 37)], 17: [(0, 36)],
    18: [(0, 37)], 19: [(0, 46), (53, 53)], 20: [(0, 53)],
    21: [(0, 53)], 22: [(0, 53)], 23: [(0, 53)], 24: [(0, 53)],
    25: [(0, 53)], 26: [(0, 52)], 27: [(0, 13), (17, 52)],
    28: [(0, 8), (17, 52)], 29: [(0, 8), (17, 52)],
    30: [(0, 8), (17, 50)], 31: [(0, 6), (17, 50)], 32: [(17, 33)],
    33: [(17, 33)], 34: [(17, 31)], 35: [(17, 31)], 36: [(17, 31)],
    37: [(17, 29)], 38: [(17, 29)], 39: [(17, 27)],
    40: [(19, 25)], 41: [(19, 25)],
}

# UW原版直接证据朝R。以下为 jp-action-b.gif 精确裁剪中的单人可见人体，run仍为闭区间。
# 构造证据：R通道>5的8连通分量中剔除左上两个泡泡分量，只保留主人体与右前臂/拳；
# 对各保留分量逐行取span，仅在同一行gap<=1时桥接。无主观补肢体、无全局填洞。
UW_OFFICIAL_R_CLEAN_RUNS = {
    1: [(18, 23)], 2: [(18, 26)], 3: [(16, 26)], 4: [(16, 26)],
    5: [(16, 26)], 6: [(12, 26)], 7: [(2, 26)], 8: [(2, 26)],
    9: [(1, 26)], 10: [(1, 29)], 11: [(1, 32)], 12: [(1, 32)],
    13: [(1, 35)], 14: [(1, 37)], 15: [(2, 37)],
    16: [(5, 24), (29, 37)], 17: [(5, 15), (28, 37)],
    18: [(5, 15), (28, 37)], 19: [(7, 13), (31, 37)],
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rows_sha(rows: list[str]) -> str:
    return sha256_bytes(("\n".join(rows) + "\n").encode("ascii"))


def points_sha(points: set[tuple[int, int]]) -> str:
    payload = ";".join(f"{x},{y}" for x, y in sorted(points)).encode("ascii")
    return sha256_bytes(payload)


def bbox(points: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not points:
        fail("空点集没有bbox")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def components4(points: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remain = set(points)
    out = []
    while remain:
        seed = min(remain)
        remain.remove(seed)
        comp = {seed}
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if q in remain:
                    remain.remove(q)
                    comp.add(q)
                    stack.append(q)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def load_mode1_points(path: Path, size: tuple[int, int]) -> set[tuple[int, int]]:
    im = Image.open(path)
    if im.mode != "1":
        fail(f"{path.name} mode={im.mode}，要求1")
    if im.size != size:
        fail(f"{path.name} size={im.size}，要求{size}")
    return {(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))}


def runs_points(runs: dict[int, list[tuple[int, int]]]) -> set[tuple[int, int]]:
    return {(x, y) for y, spans in runs.items() for x0, x1 in spans for x in range(x0, x1 + 1)}


def mirror_points(points: set[tuple[int, int]], width: int) -> set[tuple[int, int]]:
    return {(width - 1 - x, y) for x, y in points}


def normalize_points(pose: str, points: set[tuple[int, int]]) -> set[tuple[int, int]]:
    spec = POSE_SPEC[pose]
    transform = spec.get("normalize_transform", "none")
    if transform == "none":
        return set(points)
    if transform == "horizontal_flip":
        return mirror_points(points, spec["w"])
    fail(f"{pose} 未知normalize_transform={transform}")


def normalized_source(pose: str) -> Image.Image:
    spec = POSE_SPEC[pose]
    source = Image.open(REF_DIR / spec["source"]).convert("RGB")
    transform = spec.get("normalize_transform", "none")
    if transform == "horizontal_flip":
        source = source.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif transform != "none":
        fail(f"{pose} 未知normalize_transform={transform}")
    return source


def components8(points: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remain = set(points)
    out = []
    while remain:
        seed = min(remain)
        remain.remove(seed)
        comp = {seed}
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in remain:
                        remain.remove(q)
                        comp.add(q)
                        stack.append(q)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def official_uw_raw_subject(source_r: Image.Image) -> set[tuple[int, int]]:
    """从官方R向裁剪确定性恢复可见人体；返回仍为source R坐标。"""
    if source_r.size != (39, 21):
        fail(f"UW官方裁剪尺寸={source_r.size}，要求(39, 21)")
    seeds = {
        (x, y) for y in range(source_r.height) for x in range(source_r.width)
        if source_r.getpixel((x, y))[0] > 5
    }
    comps = components8(seeds)
    sizes = [len(comp) for comp in comps]
    if sizes != [326, 76, 8, 7]:
        fail(f"UW官方裁剪前景分量漂移: {sizes}")
    kept = comps[:2]  # 8px/7px两个分量是左上气泡，不属于人体。
    points = set()
    for y in range(source_r.height):
        spans = []
        for comp in kept:
            xs = [x for x, yy in comp if yy == y]
            if xs:
                spans.append((min(xs), max(xs)))
        spans.sort()
        merged = []
        for x0, x1 in spans:
            if merged and x0 - merged[-1][1] <= 2:  # 中间最多1px暗轮廓时桥接。
                merged[-1] = (merged[-1][0], x1)
            else:
                merged.append((x0, x1))
        for x0, x1 in merged:
            points.update((x, y) for x in range(x0, x1 + 1))
    explicit = runs_points(UW_OFFICIAL_R_CLEAN_RUNS)
    if points != explicit:
        fail("UW官方裁剪算法结果与显式逐行runs不一致")
    return points


def validate_provenance(pose: str) -> dict:
    spec = POSE_SPEC[pose]
    path = REF_DIR / spec["legacy_json"]
    if not path.exists() or sha256_file(path) != spec["legacy_json_sha256"]:
        fail(f"{pose} legacy mask JSON缺失或SHA不符")
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = spec["provenance"]
    for key, value in expected.items():
        if data.get(key) != value:
            fail(f"{pose} legacy provenance {key}={data.get(key)!r}，要求{value!r}")
    if data.get("referenceCropFile") != spec["source"] or data.get("referenceCropSha256") != spec["source_sha256"]:
        fail(f"{pose} legacy provenance未指向锁定参考裁剪")
    return {key: data[key] for key in expected}


def derive_subject(pose: str) -> tuple[set[tuple[int, int]], dict]:
    spec = POSE_SPEC[pose]
    size = (spec["w"], spec["h"])
    source = REF_DIR / spec["source"]
    legacy = REF_DIR / spec["legacy_mask"]
    if sha256_file(source) != spec["source_sha256"]:
        fail(f"{pose} source SHA不符")
    if sha256_file(legacy) != spec["legacy_mask_sha256"]:
        fail(f"{pose} legacy mask SHA不符")
    if Image.open(source).size != size:
        fail(f"{pose} source尺寸不符")
    validate_provenance(pose)
    old_source = load_mode1_points(legacy, size)
    old = normalize_points(pose, old_source)
    if pose == "SURF0":
        points = runs_points(SURF0_CLEAN_RUNS)
        added = sorted(points - old)
        removed = sorted(old - points)
        if len(points) != 457 or len(components4(points)) != 1 or bbox(points) != (0, 0, 30, 20):
            fail("SURF0 clean mask固定断言失败")
        if added != sorted({(19, 9), (1, 11), (25, 13), (26, 13),
                            (28, 14), (28, 15), (28, 16), (29, 17)}):
            fail(f"SURF0相对R2新增像素异常: {added}")
        if removed:
            fail(f"SURF0不应删除R2像素: {removed}")
        recipe = "显式逐行clean runs；相对R2仅补8个原图连续人物边缘；无fill_holes/平滑"
    elif pose == "JUMP_AIR":
        points = runs_points(JUMP_CLEAN_RUNS)
        added = sorted(points - old)
        removed = sorted(old - points)
        if len(points) != 1437 or len(components4(points)) != 1 or bbox(points) != (0, 0, 53, 41):
            fail("JUMP_AIR clean mask固定断言失败")
        if len(added) != 86 or len(removed) != 36:
            fail(f"JUMP增删像素异常 add={len(added)} remove={len(removed)}")
        recipe = "显式逐行clean runs；相对R2去36个天空/蓝边污染并恢复86个经原图逐像素核对的泳衣/腿脚；无fill_holes/矩形补画"
    else:
        source_r = Image.open(source).convert("RGB")
        explicit_source = official_uw_raw_subject(source_r)
        if old_source != explicit_source:
            fail("UW_NORMAL独立mask与官方裁剪确定性分割不一致")
        points = normalize_points(pose, explicit_source)
        added, removed = [], []
        if len(points) != 425 or len(components4(points)) != 1 or bbox(points) != (1, 1, 37, 19):
            fail("UW_NORMAL官方单人mask固定断言失败")
        recipe = (
            "jp-action-b.gif官方裁剪：R>5的8连通分量剔除两个气泡，仅保留人体主分量和"
            "右前臂/拳；逐分量按行span，gap<=1才桥接；无主观补肢体/全局填洞/平滑"
        )
    return points, {
        "recipe": recipe,
        "addedPixels": [list(p) for p in added],
        "removedPixels": [list(p) for p in removed],
    }


def save_mask(path: Path, size: tuple[int, int], points: set[tuple[int, int]]) -> None:
    im = Image.new("1", size, 0)
    px = im.load()
    for x, y in points:
        px[x, y] = 1
    im.save(path)


def extract_official_uw() -> None:
    """从本地官方截图重建可跟踪的UW原生裁剪和独立R向mask。"""
    spec = POSE_SPEC["UW_NORMAL"]
    original = BASE.parent / "原版参考" / "官方截图" / "jp-action-b.gif"
    if not original.exists():
        fail(f"缺少官方UW来源: {original}")
    if sha256_file(original) != spec["provenance"]["sourceSha256"]:
        fail("jp-action-b.gif SHA不符")
    frame = Image.open(original).convert("RGB")
    if list(frame.size) != spec["provenance"]["sourceOriginalSize"]:
        fail(f"jp-action-b.gif尺寸={frame.size}")
    crop_box = tuple(spec["provenance"]["maskCropBox"])
    source_r = frame.crop(crop_box)
    points_r = official_uw_raw_subject(source_r)
    REF_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r3a-uw-official-", dir=REF_DIR) as td_name:
        td = Path(td_name)
        source_temp = td / spec["source"]
        mask_temp = td / spec["legacy_mask"]
        json_temp = td / spec["legacy_json"]
        source_r.save(source_temp)
        save_mask(mask_temp, (spec["w"], spec["h"]), points_r)
        if sha256_file(source_temp) != spec["source_sha256"]:
            fail("UW官方裁剪PNG SHA漂移")
        if sha256_file(mask_temp) != spec["legacy_mask_sha256"]:
            fail("UW官方mask PNG SHA漂移")
        meta = {
            "schemaVersion": 3,
            "pose": "UW_NORMAL",
            "artifactKind": "independent-official-human-subject-mask",
            "width": spec["w"],
            "height": spec["h"],
            **spec["provenance"],
            "cleanupLog": [
                "精确裁剪内取R通道>5的8连通分量，固定面积[326,76,8,7]",
                "剔除8px/7px两个左上气泡分量，仅保留主人体326px和右前臂/拳76px",
                "各保留分量逐行取minX..maxX；同一行仅gap<=1时桥接，保留更大负空间",
                "源朝R；subject构建时明确horizontal_flip为canonical L；无缩放/平滑/全局填洞",
            ],
            "visibleBBox": list(bbox(points_r)),
            "components4": len(components4(points_r)),
            "maskSha256": sha256_file(mask_temp),
            "referenceCropFile": spec["source"],
            "referenceCropSha256": sha256_file(source_temp),
            "sourceVersion": "日版官方宣传图 jp-action-b.gif",
            "evidenceLimit": spec["evidence_limit"],
        }
        json_temp.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if sha256_file(json_temp) != spec["legacy_json_sha256"]:
            fail("UW官方mask JSON SHA漂移")
        os.replace(source_temp, REF_DIR / spec["source"])
        os.replace(mask_temp, REF_DIR / spec["legacy_mask"])
        os.replace(json_temp, REF_DIR / spec["legacy_json"])
    print(f"[extract] UW official source/mask/json -> {REF_DIR}")


def subject_meta(pose: str, points: set[tuple[int, int]], detail: dict, mask_sha: str) -> dict:
    spec = POSE_SPEC[pose]
    x0, y0, x1, y1 = bbox(points)
    negative = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)} - points
    return {
        "schemaVersion": 1,
        "stage": "3A-R3A",
        "artifactKind": "original-human-subject-mask",
        "pose": pose,
        "width": spec["w"],
        "height": spec["h"],
        "sourceFile": spec["source"],
        "sourceSha256": spec["source_sha256"],
        "legacyMaskFile": spec["legacy_mask"],
        "legacyMaskSha256": spec["legacy_mask_sha256"],
        "legacyMaskJsonFile": spec["legacy_json"],
        "legacyMaskJsonSha256": spec["legacy_json_sha256"],
        "sourceProvenance": validate_provenance(pose),
        "pixels": len(points),
        "visibleBBox": [x0, y0, x1, y1],
        "components4": len(components4(points)),
        "pointsSha256": points_sha(points),
        "negativeSpacePixels": len(negative),
        "negativeSpaceSha256": points_sha(negative),
        "maskSha256": mask_sha,
        "classifierId": CLASSIFIER_ID,
        "classifierVersion": CLASSIFIER_VERSION,
        "fillHoles": False,
        "personalized": False,
        "futureIdentityStatus": "not-defined-in-R3A",
        "reviewHeadRoiXYXY": list(spec["review_head_roi"]),
        "evidenceLimit": spec["evidence_limit"],
        **detail,
    }


def make_subjects() -> None:
    REF_DIR.mkdir(parents=True, exist_ok=True)
    derived = {pose: derive_subject(pose) for pose in POSES}
    with tempfile.TemporaryDirectory(prefix="r3a-subjects-", dir=REF_DIR) as td_name:
        td = Path(td_name)
        temp_pairs = []
        for pose in POSES:
            spec = POSE_SPEC[pose]
            points, detail = derived[pose]
            mask_temp = td / spec["subject"]
            json_temp = td / spec["subject_json"]
            save_mask(mask_temp, (spec["w"], spec["h"]), points)
            meta = subject_meta(pose, points, detail, sha256_file(mask_temp))
            json_temp.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temp_pairs.append((mask_temp, REF_DIR / spec["subject"]))
            temp_pairs.append((json_temp, REF_DIR / spec["subject_json"]))
            print(f"[subject] {pose}: {len(points)}px bbox={bbox(points)} -> {spec['subject']}")
        for temp_path, final_path in temp_pairs:
            os.replace(temp_path, final_path)


def load_subject(pose: str) -> tuple[set[tuple[int, int]], dict]:
    spec = POSE_SPEC[pose]
    mask_path = REF_DIR / spec["subject"]
    json_path = REF_DIR / spec["subject_json"]
    if not mask_path.exists() or not json_path.exists():
        fail(f"缺少{pose} R3A subject；先运行 --make-subjects")
    points = load_mode1_points(mask_path, (spec["w"], spec["h"]))
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    derived, detail = derive_subject(pose)
    if points != derived:
        fail(f"{pose} subject与显式derivation不一致")
    expected = subject_meta(pose, points, detail, sha256_file(mask_path))
    if meta != expected:
        keys = sorted({*meta, *expected})
        changed = [key for key in keys if meta.get(key) != expected.get(key)]
        fail(f"{pose} subject JSON完整合同不一致: {changed}")
    return points, meta


def nearest_key(rgb: tuple[int, int, int], palette: dict[str, tuple[int, int, int]], allowed=None) -> str:
    keys = allowed or tuple(palette)
    return min(keys, key=lambda k: sum((rgb[i] - palette[k][i]) ** 2 for i in range(3)))


def classify_pixel(pose: str, x: int, y: int, rgb: tuple[int, int, int]) -> str:
    if pose == "UW_NORMAL":
        return UW_CHAR[nearest_key(rgb, UW_RGB)]
    allowed = tuple(SURFACE_RGB)
    # SURF的白色只能来自原版唯一眼部带，避免水花/背景白被解释成人体五官。
    if pose == "SURF0" and not (11 <= x <= 15 and 7 <= y <= 9):
        allowed = tuple(k for k in allowed if k != "W")
    return nearest_key(rgb, SURFACE_RGB, allowed)


def build_master(pose: str, subject: set[tuple[int, int]]) -> list[str]:
    spec = POSE_SPEC[pose]
    source = normalized_source(pose)
    if source.size != (spec["w"], spec["h"]):
        fail(f"{pose} source尺寸变化")
    rows = []
    for y in range(spec["h"]):
        chars = []
        for x in range(spec["w"]):
            chars.append(classify_pixel(pose, x, y, source.getpixel((x, y))) if (x, y) in subject else ".")
        rows.append("".join(chars))
    return rows


def mirror_rows(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


def rows_points(rows: list[str]) -> set[tuple[int, int]]:
    return {(x, y) for y, row in enumerate(rows) for x, char in enumerate(row) if char != "."}


def review_head_points(pose: str, subject: set[tuple[int, int]], direction: str = "L") -> set[tuple[int, int]]:
    """仅供审核板隐藏头部用；这不是下一阶段允许修改的身份蒙版。"""
    spec = POSE_SPEC[pose]
    x0, y0, x1, y1 = spec["review_head_roi"]
    points = {(x, y) for x, y in subject if x0 <= x < x1 and y0 <= y < y1}
    if direction == "R":
        return {(spec["w"] - 1 - x, y) for x, y in points}
    return points


def root_for(pose: str, direction: str) -> tuple[int, int]:
    spec = POSE_SPEC[pose]
    x, y = spec["root_l"]
    return (spec["w"] - 1 - x, y) if direction == "R" else (x, y)


def render_rows(rows: list[str], hide: set[tuple[int, int]] | None = None) -> Image.Image:
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    hide = hide or set()
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == "." or (x, y) in hide:
                continue
            px[x, y] = (*RENDER_RGB[char], 255)
    return im


def checker(size: tuple[int, int], cell: int = 4) -> Image.Image:
    im = Image.new("RGB", size, (47, 47, 57))
    px = im.load()
    for y in range(size[1]):
        for x in range(size[0]):
            px[x, y] = (66, 66, 78) if ((x // cell) + (y // cell)) % 2 else (46, 46, 56)
    return im


def composite_checker(sprite: Image.Image, scale: int) -> Image.Image:
    scaled = sprite.resize((sprite.width * scale, sprite.height * scale), Image.Resampling.NEAREST)
    bg = checker(scaled.size, max(1, scale))
    bg.paste(scaled, (0, 0), scaled)
    return bg


def mask_image(size: tuple[int, int], points: set[tuple[int, int]]) -> Image.Image:
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    px = im.load()
    for x, y in points:
        px[x, y] = (245, 245, 245, 255)
    return im


def diff_image(pose: str, rows: list[str], subject: set[tuple[int, int]]) -> Image.Image:
    spec = POSE_SPEC[pose]
    source = normalized_source(pose)
    im = Image.new("RGBA", source.size, (0, 0, 0, 0))
    px = im.load()
    for y in range(spec["h"]):
        for x in range(spec["w"]):
            expected = classify_pixel(pose, x, y, source.getpixel((x, y))) if (x, y) in subject else "."
            actual = rows[y][x]
            if expected == actual and actual != ".":
                px[x, y] = (64, 220, 96, 255)
            elif expected != actual and actual == ".":
                px[x, y] = (64, 128, 255, 255)
            elif expected != actual:
                px[x, y] = (255, 64, 64, 255)
    return im


def root_bbox_image(rows: list[str], root: tuple[int, int]) -> Image.Image:
    im = render_rows(rows)
    draw = ImageDraw.Draw(im)
    pts = rows_points(rows)
    x0, y0, x1, y1 = bbox(pts)
    draw.rectangle((x0, y0, x1, y1), outline=(255, 210, 0, 255), width=1)
    x, y = root
    draw.point((x, y), fill=(255, 0, 0, 255))
    for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 <= q[0] < im.width and 0 <= q[1] < im.height:
            draw.point(q, fill=(255, 0, 0, 255))
    return im


def audit_panel(source: Image.Image, scale=8) -> Image.Image:
    if source.mode != "RGBA":
        source = source.convert("RGBA")
    return composite_checker(source, scale)


def make_audit(masters: dict[str, dict[str, list[str]]], subjects: dict[str, set[tuple[int, int]]], out: Path) -> None:
    font = ImageFont.load_default()
    columns = ("SOURCE→CANONICAL L", "SUBJECT MASK", "MASTER L", "MASTER R", "PIXEL DIFF", "BODY ONLY", "ROOT+BBOX")
    cell_w = 470
    section_h = 405
    header_h = 50
    canvas = Image.new("RGB", (24 + cell_w * len(columns), header_h + section_h * len(POSES)), (238, 238, 242))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 10), "Stage 3A R3A - ORIGINAL HUMAN MASTERS (NO YY/DAD IDENTITY)", fill=(20, 20, 24), font=font)
    draw.text((12, 27), "Native 1x at top-left of each cell; preview below is one NEAREST 8x scale.", fill=(50, 50, 58), font=font)
    for row_i, pose in enumerate(POSES):
        spec = POSE_SPEC[pose]
        y0 = header_h + row_i * section_h
        draw.rectangle((0, y0, canvas.width - 1, y0 + section_h - 1), outline=(160, 160, 168))
        source_rgb = normalized_source(pose)
        source_rgba = source_rgb.convert("RGBA")
        subject_im = mask_image(source_rgb.size, subjects[pose])
        master_l = render_rows(masters[pose]["L"])
        master_r = render_rows(masters[pose]["R"])
        diff = diff_image(pose, masters[pose]["L"], subjects[pose])
        body = render_rows(masters[pose]["L"], review_head_points(pose, subjects[pose]))
        root = root_bbox_image(masters[pose]["L"], root_for(pose, "L"))
        images = (source_rgba, subject_im, master_l, master_r, diff, body, root)
        for col_i, (label, native) in enumerate(zip(columns, images)):
            x0 = 12 + col_i * cell_w
            draw.text((x0, y0 + 8), f"{pose} / {label}", fill=(20, 20, 24), font=font)
            native_bg = checker(native.size, 1)
            native_bg.paste(native, (0, 0), native)
            canvas.paste(native_bg, (x0, y0 + 28))
            zoom = audit_panel(native, 8)
            canvas.paste(zoom, (x0, y0 + 62))
            if label == "BODY ONLY":
                draw.text((x0, y0 + 62 + zoom.height + 4),
                          "review-only head region hidden; NOT an editable identity mask",
                          fill=(80, 40, 40), font=font)
        draw.text((12, y0 + section_h - 18),
                  f"{spec['cn']} | pixels={len(subjects[pose])} | rootL={root_for(pose, 'L')} | identity=NOT APPLIED",
                  fill=(30, 30, 38), font=font)
    canvas.save(out)


def make_blind(masters: dict[str, dict[str, list[str]]], out: Path) -> None:
    font = ImageFont.load_default()
    scales = (1, 3, 8)
    width = max(
        40 + sum(POSE_SPEC[pose]["w"] * scale * 2 + 56 for pose in POSES)
        for scale in scales
    )
    y = 42
    sections = []
    for scale in scales:
        row_h = max(POSE_SPEC[p]["h"] * scale for p in POSES) + 46
        row = Image.new("RGB", (width, row_h), (24, 24, 30))
        d = ImageDraw.Draw(row)
        d.text((10, 8), f"Blind human-readability strip / exact NEAREST {scale}x", fill=(235, 235, 238), font=font)
        x = 20
        for pose in POSES:
            for direction in ("L", "R"):
                im = composite_checker(render_rows(masters[pose][direction]), scale)
                row.paste(im, (x, 28))
                x += im.width + 28
        sections.append(row)
        y += row_h + 8
    canvas = Image.new("RGB", (width, y), (16, 16, 20))
    d = ImageDraw.Draw(canvas)
    d.text((10, 10), "R3A gate: first decide whether every sprite reads as one complete person and action.", fill=(245, 245, 248), font=font)
    y0 = 42
    for row in sections:
        canvas.paste(row, (0, y0))
        y0 += row.height + 8
    canvas.save(out)


def hex_rows(points: set[tuple[int, int]], w: int, h: int) -> list[str]:
    nbytes = (w + 7) // 8
    out = []
    for y in range(h):
        bits = [1 if (x, y) in points else 0 for x in range(w)] + [0] * (nbytes * 8 - w)
        raw = []
        for i in range(0, len(bits), 8):
            byte = 0
            for bit in bits[i:i + 8]:
                byte = (byte << 1) | bit
            raw.append(f"{byte:02x}")
        out.append("".join(raw))
    return out


def bake_js(masters: dict[str, dict[str, list[str]]], subjects: dict[str, set[tuple[int, int]]], metas: dict[str, dict], out: Path) -> None:
    data = {
        "meta": {
            "schemaVersion": 1,
            "stage": "3A-R3A",
            "artifactKind": "original-human-master",
            "personalized": False,
            "generatedBy": "build_sprites_r3a.py",
            "classifierId": CLASSIFIER_ID,
            "classifierVersion": CLASSIFIER_VERSION,
            "poses": list(POSES),
            "directions": ["L", "R"],
            "integrationStatus": "not-integrated; visual gate required",
        },
        "surfacePalette": {k: "#%02X%02X%02X" % rgb for k, rgb in SURFACE_RGB.items()},
        "underwaterPalette": {UW_CHAR[k]: "#%02X%02X%02X" % rgb for k, rgb in UW_RGB.items()},
        "poses": {},
    }
    for pose in POSES:
        spec = POSE_SPEC[pose]
        entry = {
            "cn": spec["cn"],
            "w": spec["w"],
            "h": spec["h"],
            "canonicalDirection": "L",
            "sourceFacing": spec["source_facing"],
            "rootDesc": spec["root_desc"],
            "rootByDir": {d: list(root_for(pose, d)) for d in ("L", "R")},
            "visibleBBoxByDir": {d: list(bbox(rows_points(masters[pose][d]))) for d in ("L", "R")},
            "masterRowsByDir": masters[pose],
            "contentSha256ByDir": {d: rows_sha(masters[pose][d]) for d in ("L", "R")},
            "reference": {
                "cropFile": spec["source"],
                "cropSha256": spec["source_sha256"],
                "subjectMaskFile": spec["subject"],
                "subjectMaskSha256": metas[pose]["maskSha256"],
                "subjectMaskJson": spec["subject_json"],
                "subjectMaskJsonSha256": sha256_file(REF_DIR / spec["subject_json"]),
                "classifierId": CLASSIFIER_ID,
                "classifierVersion": CLASSIFIER_VERSION,
                "evidenceLimit": spec["evidence_limit"],
            },
            "subjectMaskRows": hex_rows(subjects[pose], spec["w"], spec["h"]),
            "futureIdentity": {
                "applied": False,
                "allowedMaskStatus": "not-defined-in-R3A",
                "reviewHeadRoiXYXY": list(spec["review_head_roi"]),
                "ruleForNextStage": (
                    "R3B must create and separately approve a semantic identity mask; "
                    "the reviewHeadRoi is not an edit permission; changedPixels must be a subset "
                    "of that approved mask and all pixels outside it must remain identical"
                ),
            },
        }
        data["poses"][pose] = entry
    text = "// Generated by build_sprites_r3a.py; original human masters only.\n"
    text += "const SPRITES_R3A_HUMAN = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    for token in ('"yy"', '"dd"', 'FACES', 'avatar_paint', 'identityMask', '"team"'):
        if token in text:
            fail(f"R3A JS意外含身份层标记: {token}")
    out.write_text(text, encoding="utf-8")


def selfcheck(masters: dict[str, dict[str, list[str]]], subjects: dict[str, set[tuple[int, int]]]) -> None:
    for pose in POSES:
        spec = POSE_SPEC[pose]
        subject = subjects[pose]
        expected_l = build_master(pose, subject)
        actual_l = masters[pose]["L"]
        actual_r = masters[pose]["R"]
        if actual_l != expected_l:
            fail(f"{pose}母版与参考逐像素分类器不一致")
        if actual_r != mirror_rows(actual_l):
            fail(f"{pose} R不是L严格镜像")
        if rows_points(actual_l) != subject:
            fail(f"{pose} alpha与subject mask不一致")
        if len(components4(subject)) != 1:
            fail(f"{pose}主体非单一4连通")
        allowed = set(".ODdSsWumlw")
        bad = set("".join(actual_l + actual_r)) - allowed
        if bad:
            fail(f"{pose}非法字符 {bad}")
        for direction in ("L", "R"):
            root = root_for(pose, direction)
            points = rows_points(masters[pose][direction])
            if root not in points and not any((root[0] + dx, root[1] + dy) in points
                                              for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                fail(f"{pose}/{direction} root落空")
        print(f"[check] {pose}: {len(subject)}px, bbox={bbox(subject)}, rows={rows_sha(actual_l)[:12]} PASS")


def build() -> None:
    subjects = {}
    metas = {}
    masters = {}
    for pose in POSES:
        subject, meta = load_subject(pose)
        subjects[pose] = subject
        metas[pose] = meta
        rows_l = build_master(pose, subject)
        masters[pose] = {"L": rows_l, "R": mirror_rows(rows_l)}
    selfcheck(masters, subjects)
    node = shutil.which("node")
    if not node:
        fail("找不到node，无法执行JS语法门")
    outputs = (OUT_JS, OUT_AUDIT, OUT_BLIND)
    with tempfile.TemporaryDirectory(prefix="r3a-build-", dir=BASE) as td_name:
        td = Path(td_name)
        temp = {path: td / path.name for path in outputs}
        bake_js(masters, subjects, metas, temp[OUT_JS])
        check = subprocess.run([node, "--check", str(temp[OUT_JS])], capture_output=True, text=True)
        if check.returncode:
            fail(f"node --check失败: {check.stderr[:300]}")
        make_audit(masters, subjects, temp[OUT_AUDIT])
        make_blind(masters, temp[OUT_BLIND])
        for final in outputs:
            os.replace(temp[final], final)
    print("[done] R3A原版人体母版产物生成完成；人工结论以验收记录为准；本脚本不接入主HTML")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make-subjects", action="store_true")
    parser.add_argument("--extract-official-uw", action="store_true")
    args = parser.parse_args()
    try:
        if args.extract_official_uw:
            extract_official_uw()
        elif args.make_subjects:
            make_subjects()
        else:
            build()
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
