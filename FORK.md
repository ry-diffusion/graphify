# This fork

A personal build of graphify for Elixir/Phoenix + Svelte codebases. It is upstream
**v0.9.73** plus three upstream pull requests that were open and conflicting
with `v8` when this was cut, and one fix of ours. Nothing else differs.

Install:

```bash
uv tool install --force "graphifyy @ git+https://github.com/ry-diffusion/graphify@elixir-svelte"
```

After switching from the PyPI build, delete `graphify-out/` and build again:
the AST cache keeps the previous extractor's output per file hash, and an
incremental update would replay it.

## What is in it

| commit | origin | what it fixes |
|---|---|---|
| `fix(elixir): walk single-line def … do:` | [#2970](https://github.com/Graphify-Labs/graphify/pull/2970) by @rajatnagda45, ported | calls made from `def f(x), do: g(x)` were never walked |
| `feat(extract): give .svelte a real AST pass` | [#2731](https://github.com/Graphify-Labs/graphify/pull/2731) by @RepairYourTech, Svelte half only | `.svelte` was fed whole to the JS grammar, so only imports survived (issue [#3928](https://github.com/Graphify-Labs/graphify/issues/3928)); also normalizes `import type` as the `.vue` path does |
| `feat(elixir): resolve Module.function() remote calls` + `never guess a stdlib receiver` | [#2717](https://github.com/Graphify-Labs/graphify/pull/2717) by @prtngn | `Repo.insert(x)` became a bare `insert` and never crossed files; ExUnit bodies were not walked |
| `fix(elixir): a bare call crosses files only to a module the caller imports` | ours | the global name pass bound any unqualified call (`count(e.id)` in an Ecto query, `json(conn, _)` from `use Phoenix.Controller`) to the one same-named def in the corpus |
| `feat(elixir): remote calls on by default` | ours | the #2717 resolver was opt-in (`GRAPHIFY_ELIXIR_REMOTE_CALLS=1`); git hooks and agents never set it. `=0` turns it off |

Conflicts were resolved by hand where upstream had moved on: #2731's Astro
masking was dropped because upstream already ships `_astro_mask_non_script`
(#3902), and its leftover `.astro` branch in `_parse_js_tree` (which called the
dropped helper inside a `try`, failing silently) was removed.

## Measured (a private Phoenix + Svelte 5 app, ~2,800 code files)

| | v0.9.73 | this fork |
|---|---:|---:|
| Elixir calls across files | 396 (all name guesses) | 4,866 (all read from the call) |
| … landing on an unrelated `count()` | 129 | 1 |
| ExUnit spec → `lib/` calls | 13 | 2,057 |
| `.svelte` nodes | 910 | 3,434 |
| `.svelte` partial-parse warnings | 517 | 0 |
| `affected` on its cache module, depth 2 | 29 | 317 |

Test suite: the same 57 failures as a clean v0.9.73 checkout in this
environment (optional grammars such as Terraform, VB.NET, R, Solidity, Erlang
not installed), plus the new tests passing.

When upstream merges these, this fork should go away.
