---
id: playground
title: Online Playground
---

The **Diagrams Playground** is a free online editor for the **diagrams** library. Write Diagram as Code in Python and see the rendered architecture diagram appear next to it — in your web browser, with nothing to install.

> **[Open the Playground →](/playground/)**

## Why use it

Installing **diagrams** locally means installing Python *and* [Graphviz](https://www.graphviz.org/). The playground skips both, which makes it handy when you want to:

- try **diagrams** before installing anything,
- sketch a cloud architecture diagram from a laptop that isn't set up for Python,
- share a working diagram with a teammate as a single link,
- look up which node classes exist for AWS, Azure, GCP, Kubernetes and the other providers.

## What it can do

- **Live preview** — the diagram re-renders as you type.
- **Node browser** — search every available node, or browse the full provider → category tree, and click to insert the matching `import`.
- **Autocompletion** — import paths and node names complete as you type, with signature hints for `Diagram`, `Cluster` and `Edge`.
- **Export** — download the result as PNG, SVG or JPEG at a size you choose, or copy the image straight to your clipboard.
- **Share links** — the whole diagram is encoded into the URL, so sending the link is enough. Nothing is stored on a server.
- **Examples** — start from a ready-made diagram instead of a blank editor.

## How it works

The playground runs the real **diagrams** package — not a reimplementation — inside your browser using [Pyodide](https://pyodide.org), which is CPython compiled to WebAssembly. Graph layout is done by a WebAssembly build of Graphviz.

Everything executes locally in the browser tab: your code is never uploaded, and there is no backend. The first visit downloads the Python runtime, so it takes a few seconds; after that it is cached.

## When to install instead

The playground is for quick work and sharing. Install the library ([installation guide](/docs/getting-started/installation)) when you want to:

- keep diagrams in version control next to your code,
- generate diagrams in CI or a build script,
- use custom local icons, or
- work offline.

The Python code is identical either way, so anything you write in the playground runs unchanged after `pip install diagrams`.
