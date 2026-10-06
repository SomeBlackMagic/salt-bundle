"""Generate index.html from repository index."""

from datetime import datetime

from ..dependencies.index_models import Index


def render_index_html(index: Index) -> str:
    """Render a static HTML page listing all packages and versions."""

    rows = []
    for name in sorted(index.packages):
        entries = index.packages[name]
        for entry in entries:
            badge = "formula" if entry.type == "formula" else "extension"
            badge_cls = "badge-formula" if entry.type == "formula" else "badge-ext"
            created = entry.created.strftime("%Y-%m-%d") if entry.created else ""
            rows.append(
                f'<tr>'
                f'<td>{name}</td>'
                f'<td>{entry.version}</td>'
                f'<td><span class="{badge_cls}">{badge}</span></td>'
                f'<td>{created}</td>'
                f'<td><a href="{entry.url}">download</a></td>'
                f'</tr>'
            )

    generated = index.generated.strftime("%Y-%m-%d %H:%M:%S UTC")
    total_packages = len(index.packages)
    total_versions = sum(len(v) for v in index.packages.values())
    table_body = "\n        ".join(rows) if rows else '<tr><td colspan="5">No packages</td></tr>'

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Salt Bundle Package Index</title>
  <style>
    :root {{
      --bg: #f8f9fa;
      --fg: #212529;
      --border: #dee2e6;
      --link: #0d6efd;
      --header-bg: #343a40;
      --header-fg: #fff;
      --row-hover: #e9ecef;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--fg); padding: 2rem; }}
    h1 {{ margin-bottom: .25rem; }}
    .meta {{ color: #6c757d; margin-bottom: 1.5rem; font-size: .9rem; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }}
    th {{ background: var(--header-bg); color: var(--header-fg); text-align: left; padding: .75rem 1rem; }}
    td {{ padding: .6rem 1rem; border-top: 1px solid var(--border); }}
    tr:hover td {{ background: var(--row-hover); }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .badge-formula, .badge-ext {{
      display: inline-block; padding: .15rem .5rem; border-radius: 4px;
      font-size: .8rem; font-weight: 600;
    }}
    .badge-formula {{ background: #d1ecf1; color: #0c5460; }}
    .badge-ext {{ background: #d4edda; color: #155724; }}
  </style>
</head>
<body>
  <h1>Salt Bundle Package Index</h1>
  <p class="meta">{total_packages} package(s), {total_versions} version(s) &middot; generated {generated}</p>
  <table>
    <thead>
      <tr>
        <th>Package</th>
        <th>Version</th>
        <th>Type</th>
        <th>Created</th>
        <th>Archive</th>
      </tr>
    </thead>
    <tbody>
        {table_body}
    </tbody>
  </table>
</body>
</html>
"""
