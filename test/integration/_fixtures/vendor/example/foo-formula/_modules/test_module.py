def ping():
    return "module loaded"


def use_utils():
    return __utils__["test_utils.hello"]()


def probe_loaders():
    """Exercise every formula namespace through Salt's loader in the minion."""
    import salt.loader

    cases = {
        "beacons": ("beacon", "beacons_dirs", "test_beacon.validate", ([],)),
        "engines": ("engine", "engines_dirs", "test_engine.probe", ()),
        "executors": ("executor", "executor_dirs", "test_executor.run", ()),
        "matchers": ("matcher", "matchers_dirs", "test_matcher.match", ("*",)),
        "serializers": ("serializer", "serializers_dirs", "test_serializer.serialize", ("loaded",)),
        "tops": ("top", "top_dirs", "test_top.top", ()),
        "pillar": ("pillar", "pillar_dirs", "test_pillar.ext_pillar", ("kitchen-target", {})),
        "cache": ("cache", "cache_dirs", "test_cache.fetch", ("test-bank", "test-key", "/tmp")),
        "sdb": ("sdb", "sdb_dirs", "test_sdb.get", ("test-key",)),
    }
    results = {}
    for namespace, (tag, entrypoint, function, args) in cases.items():
        try:
            paths = salt.loader._module_dirs(
                __opts__, namespace, tag, ext_type_dirs=entrypoint
            )
            loader = salt.loader.LazyLoader(paths, __opts__, tag=tag)
            results[namespace] = loader[function](*args)
        except Exception as exc:
            results[namespace] = f"{type(exc).__name__}: {exc}"
    try:
        results["wrapper"] = salt.loader.ssh_wrapper(__opts__)["test_wrapper.ping"]()
    except Exception as exc:
        results["wrapper"] = f"{type(exc).__name__}: {exc}"
    return results
