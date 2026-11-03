"""SVG generator for HLS compiler: DAG -> SVG picture, standard library only"""
from __future__ import annotations

import math

from hls.dag import DAG

GAP = 90       # px between rows and between columns
RADIUS = 24    # px, size of a node


def dag_to_svg(dag: DAG) -> str:
    # row: inputs on top, each node one row below its deepest operand
    row = {name: 0 for name in dag.inputs}
    for name, node in dag.nodes.items():
        row[name] = 1 + max(row[node.eq.lhs], row[node.eq.rhs])

    # column: order within the row, rows centered
    col, count = {}, {}
    for name in row:
        col[name] = count.get(row[name], 0)
        count[row[name]] = col[name] + 1
    widest = max(count.values(), default=1)
    pos = {name: (60 + (col[name] + (widest - count[row[name]]) / 2) * GAP,
                  40 + row[name] * GAP) for name in row}

    width = 120 + (widest - 1) * GAP
    height = 80 + max(row.values(), default=0) * GAP
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" '
           f'font-family="monospace" font-size="13" text-anchor="middle">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
           'markerWidth="7" markerHeight="7" orient="auto">'
           '<path d="M0,0 L10,5 L0,10 z"/></marker></defs>']

    # edges: operand -> node, trimmed so they stop at the shapes' edges
    for name, node in dag.nodes.items():
        x2, y2 = pos[name]
        for operand in (node.eq.lhs, node.eq.rhs):
            x1, y1 = pos[operand]
            d = math.hypot(x2 - x1, y2 - y1)
            ux, uy = (x2 - x1) / d, (y2 - y1) / d
            svg.append(f'<line x1="{x1 + ux * RADIUS:.1f}" y1="{y1 + uy * RADIUS:.1f}" '
                       f'x2="{x2 - ux * RADIUS:.1f}" y2="{y2 - uy * RADIUS:.1f}" '
                       f'stroke="black" marker-end="url(#arrow)"/>')

    # inputs as boxes, operations as circles with op and name
    for name in dag.inputs:
        x, y = pos[name]
        svg.append(f'<rect x="{x - RADIUS}" y="{y - RADIUS * 0.7:.1f}" width="{2 * RADIUS}" '
                   f'height="{1.4 * RADIUS:.1f}" fill="#eef" stroke="black"/>'
                   f'<text x="{x}" y="{y + 5}">{name}</text>')
    for name, node in dag.nodes.items():
        x, y = pos[name]
        svg.append(f'<circle cx="{x}" cy="{y}" r="{RADIUS}" fill="#ffe" stroke="black"/>'
                   f'<text x="{x}" y="{y - 3}">{node.eq.op}</text>'
                   f'<text x="{x}" y="{y + 12}">{name}</text>')

    svg.append("</svg>")
    return "\n".join(svg)
