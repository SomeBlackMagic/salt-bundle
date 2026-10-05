"""Custom state module for managing Nginx virtual hosts."""


def enabled(name, source, template="jinja", **kwargs):
    """Ensure an Nginx site is enabled.

    name
        The site name (used as filename in sites-enabled).
    source
        Salt source path for the site config template.
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    sites_available = f"/etc/nginx/sites-available/{name}"
    sites_enabled = f"/etc/nginx/sites-enabled/{name}"

    managed = __states__["file.managed"](
        name=sites_available,
        source=source,
        template=template,
        **kwargs,
    )

    if not managed["result"]:
        return managed

    if managed["changes"]:
        ret["changes"]["config"] = managed["changes"]

    link = __states__["file.symlink"](
        name=sites_enabled,
        target=sites_available,
    )

    if not link["result"]:
        ret["result"] = False
        ret["comment"] = link["comment"]
        return ret

    if link["changes"]:
        ret["changes"]["enabled"] = True

    if ret["changes"]:
        ret["comment"] = f"Site {name} configured and enabled"
    else:
        ret["comment"] = f"Site {name} is already configured"

    return ret
