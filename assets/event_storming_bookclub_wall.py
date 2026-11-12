#!/usr/bin/env python3
"""Draws assets/event_storming_bookclub_wall.svg: the public book club
(macula-services/mcl-bookclub) on a design-level storming wall in the Macula
lane form described in philosophy/EVENT_STORMING.md.

Lanes are roles and services. One enlarged blue sticky is one desk. The event
a desk produces sits on its right edge as an output port; the policy that
triggers a desk sits on its left edge as an input port. An arrow from an event
port to a policy port is a process manager; into the mesh lane it is an
emitter; onto a green sticky it is a projection.

Every name below is a folder of the book club as it is on main; change the
tables, not the drawing code, when the club changes. Run with python3, no
dependencies. The SVG is committed; this script is how it is made again.
"""
from __future__ import annotations

import pathlib

# ---- the wall, as data ----------------------------------------------------

LANES = [  # (key, label, height)
    ("organiser", "Organiser", 260),
    ("member", "Member", 260),
    ("read", "What people ask (PRJ → QRY)", 170),
    ("mesh", "Other services, over the mesh", 130),
]

# Desks left to right follow the timeline of a club's life. Each desk names
# its lane, the event it produces, the policy on its input port (if any), the
# green sticky its event feeds, and whether the event leaves the club.
DESKS = [
    dict(name="initiate_bookclub", lane="organiser", event="bookclub_initiated_v1",
         feeds="clubs"),
    dict(name="register_member", lane="member", event="member_registered_v1",
         feeds="members", emits=True),
    dict(name="procure_book", lane="organiser", event="book_procured_v1",
         feeds="books", emits=True),
    dict(name="start_reading", lane="member", event="reading_started_v1",
         feeds="readings"),
    dict(name="finish_reading", lane="member", event="reading_finished_v1",
         feeds="readings"),
    dict(name="plan_party", lane="organiser", event="party_planned_v1",
         policy="on member registered,\nmaybe plan party", hotspot=True),
    dict(name="unregister_member", lane="member", event="member_unregistered_v1",
         feeds="members"),
    dict(name="retire_book", lane="organiser", event="book_retired_v1",
         feeds="books", emits=True),
    dict(name="archive_bookclub", lane="organiser", event="bookclub_archived_v1",
         feeds="clubs"),
]

# The policy arrow: which event port feeds which desk's policy port, and the
# folder that arrow is in the code.
POLICIES = [("member_registered_v1", "plan_party", "on_member_registered_v1_maybe_plan_party/")]

READ_MODELS = [  # (key, table, queries), drawn left to right in this order
    ("clubs", "clubs", ["get_bookclub_by_id"]),
    ("members", "members", ["get_member_by_id"]),
    ("books", "books", ["get_book_by_id"]),
    ("readings", "readings", ["get_reading_by_id", "get_readings_by_member"]),
]

HOTSPOT_TEXT = ["party planned:", "leaves the club?", "not decided"]

# ---- geometry and colours -------------------------------------------------

W = 1920
TOP = 100
LANE_LABEL_W = 150
COL_X0 = LANE_LABEL_W + 60
COL_W = 176
ROW_STEP = 118            # two rows per lane; neighbours in a lane alternate
NODE_W, NODE_H = 140, 78
PORT_W, PORT_H = 118, 36
PORT_OVERLAP = 18
GREEN_W, GREEN_H = 250, 96
PINK_W, PINK_H = 250, 54

BLUE, ORANGE, LILAC = "#8EC5FF", "#FFB347", "#C9A6EC"
GREEN, PINK_WIDE, PINK_HOT = "#A9E5A3", "#F7BFD6", "#FF4FA3"
INK, MUTED, PAPER = "#1B1F24", "#4B5563", "#FFFFFF"
LANE_A, LANE_B, LANE_LINE = "#F6F7F9", "#EDF0F4", "#C9CED6"
ARROW, PM_ARROW, EMIT_ARROW = "#8A96A3", "#6D4C9F", "#B0276F"

FONT = "Inter, 'Noto Sans', 'Liberation Sans', sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', monospace"


def lane_tops() -> dict[str, tuple[int, int]]:
    y = TOP
    out = {}
    for key, _label, h in LANES:
        out[key] = (y, h)
        y += h
    return out


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, fill=INK, weight="normal", anchor="start", font=FONT, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def mono_w(s: str, size: float) -> float:
    """Width of s in the mono font, close enough to size a sticky around it."""
    return len(s) * size * 0.62


def sans_w(s: str, size: float) -> float:
    return len(s) * size * 0.52


def group(kind: str, name: str, inner: list[str], **data) -> str:
    """One tagged group per thing on the wall, so a reader of the SVG (or a
    renderer that stages the wall) can pick a kind of note by class and a
    note by data-name. Positions ride along as data-* for the same reason."""
    attrs = "".join(f' data-{k}="{v}"' for k, v in data.items())
    return f'<g class="k-{kind}" data-name="{esc(name)}"{attrs}>' + "".join(inner) + "</g>"


def sticky(x, y, w, h, fill, rotate=0.0):
    tr = f' transform="rotate({rotate} {x + w / 2} {y + h / 2})"' if rotate else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" '
            f'stroke="{INK}" stroke-opacity="0.18"{tr}/>')


def marker_id(stroke: str) -> str:
    return "head-" + stroke.lstrip("#").lower()


def markers() -> str:
    # One arrowhead per stroke colour: browsers do not all know context-stroke.
    return "<defs>" + "".join(
        f'<marker id="{marker_id(c)}" markerWidth="8" markerHeight="8" refX="7" refY="4" '
        f'orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker>'
        for c in (ARROW, PM_ARROW, EMIT_ARROW)) + "</defs>"


def curve_down(x1, y1, x2, y2, stroke, dash="", width=1.6, bend=60, opacity=1.0):
    d = f"M {x1} {y1} C {x1} {y1 + bend}, {x2} {y2 - bend}, {x2} {y2}"
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-opacity="{opacity}"{dash_attr} marker-end="url(#{marker_id(stroke)})"/>')


def build() -> str:
    lanes = lane_tops()
    y_end = TOP + sum(h for _, _, h in LANES)
    total_h = y_end + 80
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}" '
             f'viewBox="0 0 {W} {total_h}" font-family="{FONT}">',
             markers(),
             f'<rect class="paper" width="{W}" height="{total_h}" fill="{PAPER}"/>']

    # Title.
    parts.append(group("title", "title", [
        text(40, 44, "The book club on the wall", 26, weight="700"),
        text(40, 72, "Lanes for roles and services. One blue sticky per desk, its event "
                     "on the right edge as an output, a policy on the left edge as an input. "
                     "Every name is a folder in macula-services/mcl-bookclub.", 14, MUTED)]))

    # Lanes.
    for i, (key, label, h) in enumerate(LANES):
        y0, _ = lanes[key]
        parts.append(group("lane", key, [
            f'<rect x="40" y="{y0}" width="{W - 80}" height="{h}" '
            f'fill="{LANE_A if i % 2 == 0 else LANE_B}"/>',
            f'<line x1="40" y1="{y0}" x2="{W - 40}" y2="{y0}" stroke="{LANE_LINE}"/>',
            text(56, y0 + 28, label, 15, INK, "600")], x=40, y=y0, w=W - 80, h=h))
    parts.append(group("lane", "bottom", [
        f'<line x1="40" y1="{y_end}" x2="{W - 40}" y2="{y_end}" stroke="{LANE_LINE}"/>']))

    # Legend and the time note, under the lanes.
    legend = [(BLUE, "command, one desk"), (ORANGE, "event it produces"),
              (LILAC, "policy that triggers it"), (GREEN, "read model and its queries"),
              (PINK_WIDE, "fact published on the mesh"), (PINK_HOT, "hot spot, an open question")]
    items = []
    for i, (fill, label) in enumerate(legend):
        x, y = 56 + i * 235, y_end + 22
        items += [sticky(x, y, 18, 14, fill), text(x + 26, y + 12, label, 12, MUTED)]
    items.append(text(W - 44, y_end + 58, "time runs left to right, a club's life from initiate to archive",
                      12, MUTED, anchor="end"))
    parts.append(group("legend", "legend", items))

    # Desk nodes and their ports. Neighbours in one lane alternate rows so a
    # desk's event port never runs into the next desk. Every sticky is sized
    # around its text, never the other way round.
    port_at: dict[str, tuple[float, float, float, float]] = {}  # event -> (x_right, y_mid, y_bottom, w)
    policy_at: dict[str, tuple[float, float]] = {}       # desk -> (x_left, y_mid)
    row_count: dict[str, int] = {}
    for i, d in enumerate(DESKS):
        y0, _h = lanes[d["lane"]]
        row = row_count.get(d["lane"], 0)
        row_count[d["lane"]] = row + 1
        x = COL_X0 + i * COL_W
        y = y0 + 16 + (row % 2) * ROW_STEP
        nw = max(NODE_W, mono_w(d["name"], 12.5) + 20)
        parts.append(group("desk", d["name"], [
            sticky(x, y, nw, NODE_H, BLUE),
            text(x + nw / 2, y + 26, d["name"], 12.5, INK, "700", "middle", MONO)],
            x=x, y=y, w=nw, h=NODE_H, fill=BLUE, lane=d["lane"]))
        # event port on the right edge, lower half
        pw = max(PORT_W, mono_w(d["event"], 10.5) + 16)
        px, py = x + nw - PORT_OVERLAP, y + NODE_H - PORT_H - 4
        parts.append(group("event", d["event"], [
            sticky(px, py, pw, PORT_H, ORANGE),
            text(px + pw / 2, py + PORT_H / 2 + 4, d["event"], 10.5, INK, "normal", "middle", MONO)],
            x=px, y=py, w=pw, h=PORT_H, fill=ORANGE, desk=d["name"]))
        port_at[d["event"]] = (px + pw, py + PORT_H / 2, py + PORT_H, pw)
        # policy port on the left edge, lower half
        if d.get("policy"):
            lines = d["policy"].split("\n")
            qw = max(PORT_W, max(sans_w(l, 10.5) for l in lines) + 16)
            qx, qy = x - qw + PORT_OVERLAP, py
            items = [sticky(qx, qy, qw, PORT_H, LILAC)]
            for k, line in enumerate(lines):
                items.append(text(qx + qw / 2 - 8, qy + 15 + k * 13, line, 10.5, INK, "normal", "middle"))
            parts.append(group("policy", d["name"], items, x=qx, y=qy, w=qw, h=PORT_H, fill=LILAC))
            policy_at[d["name"]] = (qx, qy + PORT_H / 2)
        if d.get("hotspot"):
            hx, hy = px + pw + 16, py - 12
            items = [sticky(hx, hy, 104, 56, PINK_HOT, rotate=-8)]
            for k, line in enumerate(HOTSPOT_TEXT):
                items.append(text(hx + 52, hy + 20 + k * 14, line, 10.5, "#FFFFFF", "normal",
                                  "middle", extra=f' transform="rotate(-8 {hx + 52} {hy + 28})"'))
            parts.append(group("hotspot", d["event"], items, x=hx, y=hy, w=104, h=56, fill=PINK_HOT))

    # Read models: four green stickies, evenly spaced across the read lane.
    ry0, rh = lanes["read"]
    green_at: dict[str, tuple[float, float]] = {}
    span_x0, span_x1 = COL_X0 + 40, W - 80 - GREEN_W
    for k, (key, table, queries) in enumerate(READ_MODELS):
        gx = span_x0 + k * (span_x1 - span_x0) / (len(READ_MODELS) - 1)
        gy = ry0 + (rh - GREEN_H) / 2 + 8
        items = [sticky(gx, gy, GREEN_W, GREEN_H, GREEN),
                 text(gx + GREEN_W / 2, gy + 24, f"{table} table", 13, INK, "700", "middle")]
        for j, q in enumerate(queries):
            items.append(text(gx + GREEN_W / 2, gy + 46 + j * 17, q, 11.5, INK, "normal", "middle", MONO))
        parts.append(group("readmodel", table, items, x=gx, y=gy, w=GREEN_W, h=GREEN_H, fill=GREEN,
                           queries=" ".join(queries)))
        green_at[key] = (gx + GREEN_W / 2, gy)

    # Projections: event port -> green sticky, thin and dashed.
    for d in DESKS:
        if d.get("feeds"):
            x1, _ymid, ybot, pw = port_at[d["event"]]
            x2, y2 = green_at[d["feeds"]]
            parts.append(group("arrow-projection", f'{d["event"]}->{d["feeds"]}', [
                curve_down(x1 - pw / 2, ybot, x2, y2 - 2, ARROW, dash="4 4", width=1.2, bend=90, opacity=0.8)]))

    # Emitters: the three facts, evenly spaced in the mesh lane.
    my0, mh = lanes["mesh"]
    emitting = [d for d in DESKS if d.get("emits")]
    span_x0, span_x1 = COL_X0 + 160, W - 80 - PINK_W - 120
    for k, d in enumerate(emitting):
        px = span_x0 + k * (span_x1 - span_x0) / (len(emitting) - 1)
        py = my0 + (mh - PINK_H) / 2 + 6
        parts.append(group("fact", d["event"], [
            sticky(px, py, PINK_W, PINK_H, PINK_WIDE),
            text(px + PINK_W / 2, py + 22, f"{d['event']} fact", 11.5, INK, "700", "middle", MONO),
            text(px + PINK_W / 2, py + 41, f"emit_{d['event']}_to_mesh/", 10.5, MUTED, "normal", "middle", MONO)],
            x=px, y=py, w=PINK_W, h=PINK_H, fill=PINK_WIDE, folder=f"emit_{d['event']}_to_mesh"))
        x1, _ymid, ybot, _pw = port_at[d["event"]]
        parts.append(group("arrow-emit", d["event"], [
            curve_down(x1 - 20, ybot, px + PINK_W / 2, py - 2, EMIT_ARROW, width=1.8, bend=120)]))

    # Process managers: event port -> policy port, drawn last so it sits on top.
    for event, desk, folder in POLICIES:
        x1, y1, _, _ = port_at[event]
        x2, y2 = policy_at[desk]
        midx = (x1 + x2) / 2
        parts.append(group("arrow-policy", folder.rstrip("/"), [
            f'<path d="M {x1} {y1} C {midx} {y1}, {midx} {y2}, {x2 - 2} {y2}" '
            f'fill="none" stroke="{PM_ARROW}" stroke-width="2.2" marker-end="url(#{marker_id(PM_ARROW)})"/>',
            text(x2 - 10, y2 - 28, folder, 10.5, PM_ARROW, "normal", "end", MONO)]))

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    out = pathlib.Path(__file__).with_suffix(".svg")
    out.write_text(build() + "\n")
    print(out)
