"""A bare Elixir call (`count(x)`, no receiver) is never a cross-file call by
name alone.

Elixir resolves an unqualified call to the caller's own module, to a module the
file `import`s / `use`s, or to Kernel. The shared global pass bound it to ANY
same-named function in the corpus: on a Phoenix app every Ecto `count(e.id)`
inside a query and every `json(conn, …)` from `use Phoenix.Controller` landed on
an unrelated `count/1` or `json/2` defined in some other module — 508 of 622
such edges in one repo had no import of the target module at all.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extract import extract


def _calls(tmp_path: Path, files: dict[str, str]) -> set[tuple[str, str, str]]:
    # Under lib/, as in a real project: a top-level `stats.ex` would get the
    # file id `stats`, the same id as the bare import target `Stats`.
    paths = []
    (tmp_path / "lib").mkdir()
    for name, body in files.items():
        p = tmp_path / "lib" / name
        p.write_text(body, encoding="utf-8")
        paths.append(p)
    r = extract(paths, cache_root=tmp_path)
    label = {n["id"]: n["label"] for n in r["nodes"]}
    src = {n["id"]: n.get("source_file", "") for n in r["nodes"]}
    return {
        (label[e["source"]], label[e["target"]], Path(src[e["target"]]).name)
        for e in r["edges"]
        if e["relation"] == "calls" and src.get(e["source"]) != src.get(e["target"])
    }


def test_bare_call_without_import_does_not_cross_files(tmp_path):
    calls = _calls(tmp_path, {
        "stats.ex": "defmodule Stats do\n  def count(x), do: length(x)\nend\n",
        "report.ex": (
            "defmodule Report do\n"
            "  import Ecto.Query\n"
            "  def total(q), do: from(e in q, select: count(e.id))\n"
            "end\n"
        ),
    })
    assert not any(c[:2] == ("total()", "count()") for c in calls)


def test_bare_call_with_import_of_the_module_still_resolves(tmp_path):
    calls = _calls(tmp_path, {
        "stats.ex": "defmodule Stats do\n  def count(x), do: length(x)\nend\n",
        "report.ex": (
            "defmodule Report do\n"
            "  import Stats\n"
            "  def total(xs), do: count(xs)\n"
            "end\n"
        ),
    })
    assert ("total()", "count()", "stats.ex") in calls


def test_bare_call_picks_the_imported_module_among_namesakes(tmp_path):
    calls = _calls(tmp_path, {
        "stats.ex": "defmodule Stats do\n  def count(x), do: length(x)\nend\n",
        "other.ex": "defmodule Other do\n  def count(x), do: x\nend\n",
        "report.ex": (
            "defmodule Report do\n"
            "  import Other\n"
            "  def total(xs), do: count(xs)\n"
            "end\n"
        ),
    })
    count_edges = {c for c in calls if c[:2] == ("total()", "count()")}
    assert count_edges == {("total()", "count()", "other.ex")}
