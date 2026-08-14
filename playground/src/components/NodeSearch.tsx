import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { providerLabel } from "../search/providerLabel";
import { searchCatalog, type SearchHit } from "../search/search";
import { catalogTree } from "../search/tree";
import type { Catalog } from "../types";

interface Props {
  catalog: Catalog | null;
  onInsert: (importStmt: string) => void;
  /** Resizable sidebar width in px (see DragHandle); falls back to CSS. */
  width?: number;
}

interface MenuHit {
  name: string;
  importStmt: string;
}

interface MenuState {
  x: number;
  y: number;
  hit: MenuHit;
}

interface HitRowProps {
  icon: string;
  name: string;
  importStmt: string;
  module?: string;
  onInsert: (importStmt: string) => void;
  onContextMenu: (x: number, y: number, hit: MenuHit) => void;
  // Set only when rendered as a class row inside an expanded tree category
  // (depth 2); the container carries the indent/rail, this only tweaks the
  // row's own padding via the "is-tree-class" CSS class.
  inTree?: boolean;
}

// Shared row for a single class: real node icon (bare, no wrapper box),
// name, optional module path. Fixed layout that never shifts on hover —
// used by both the flat search results and the expanded-category tree rows
// so the two views stay visually unified. Left-click inserts the import;
// right-click opens a small custom context menu (Copy/Insert) owned by the
// parent NodeSearch.
function HitRow({ icon, name, importStmt, module, onInsert, onContextMenu, inTree }: HitRowProps) {
  return (
    <li
      className={inTree ? "hit-row is-tree-class" : "hit-row"}
      tabIndex={0}
      role="button"
      onClick={() => onInsert(importStmt)}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onInsert(importStmt);
        }
      }}
      onContextMenu={(e) => {
        e.preventDefault();
        onContextMenu(e.clientX, e.clientY, { name, importStmt });
      }}
    >
      <span className="hit-icon">
        <img src={`icons/${icon}`} width={20} height={20} alt="" loading="lazy" />
      </span>
      <span className="hit-name" title={importStmt}>{name}</span>
      {module !== undefined && <span className="hit-module">{module}</span>}
    </li>
  );
}

interface ContextMenuProps {
  x: number;
  y: number;
  hit: MenuHit;
  onInsert: (importStmt: string) => void;
  onClose: () => void;
}

// Small custom right-click menu: Copy import / Insert import. Rendered via a
// portal straight onto <body> — several ancestors (e.g. `.node-search`'s
// fade-slide entrance animation) end their animation with a lingering
// `transform`, which per spec establishes a new containing block for any
// `position: fixed` descendant. Left in place, that made the menu position
// itself relative to the sidebar instead of the viewport (appearing far from
// the click) and clipped it under `.node-search`'s `overflow: hidden` and
// the editor's stacking context (covered instead of on top). Portaling to
// `document.body` sidesteps all of that: `position: fixed` is now always
// viewport-relative, and a high z-index guarantees it paints above the
// editor. Closes on outside pointerdown, Esc, or scroll (capture-phase
// listeners so scrolling inside the results list — which doesn't bubble —
// still closes it); these still work unchanged since `rootRef` points at the
// real portaled DOM node regardless of where in the tree it renders.
function ContextMenu({ x, y, hit, onInsert, onClose }: ContextMenuProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handlePointerDown(e: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) onClose();
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    function handleScroll() {
      onClose();
    }
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    window.addEventListener("scroll", handleScroll, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("scroll", handleScroll, true);
    };
  }, [onClose]);

  return createPortal(
    <div className="ctx-menu" style={{ left: x, top: y }} ref={rootRef} role="menu">
      <button
        type="button"
        role="menuitem"
        onClick={() => {
          void navigator.clipboard.writeText(hit.importStmt).catch(() => {});
          onClose();
        }}
      >
        Copy import
      </button>
      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onInsert(hit.importStmt);
          onClose();
        }}
      >
        Insert import
      </button>
    </div>,
    document.body
  );
}

const MENU_WIDTH = 160;
const MENU_HEIGHT = 76;

// Centered SVG chevron shared by both tree levels. Unlike the old text
// glyphs ("▸"/"▾"), the triangle is geometrically centered in its box, so
// the CSS 90° open-rotation spins in place instead of drifting (the glyph's
// off-center metrics were visibly shifting the depth-1 caret mid-turn).
function Chevron() {
  return (
    <span className="tree-chevron" aria-hidden="true">
      <svg width="11" height="11" viewBox="0 0 10 10" fill="currentColor">
        <path d="M3 1.6 7.4 5 3 8.4Z" />
      </svg>
    </span>
  );
}

export default function NodeSearch({ catalog, onInsert, width }: Props) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [menu, setMenu] = useState<MenuState | null>(null);

  const hits = useMemo(
    () => (catalog ? searchCatalog(catalog, query) : []),
    [catalog, query]
  );
  const tree = useMemo(() => (catalog ? catalogTree(catalog) : []), [catalog]);

  function toggle(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  // One menu instance at a time: keep it fully on-screen by clamping against
  // the viewport rather than letting it render past the right/bottom edge.
  function openMenu(x: number, y: number, hit: MenuHit) {
    const clampedX = Math.min(x, window.innerWidth - MENU_WIDTH - 8);
    const clampedY = Math.min(y, window.innerHeight - MENU_HEIGHT - 8);
    setMenu({ x: Math.max(8, clampedX), y: Math.max(8, clampedY), hit });
  }

  // Flat search-result row (non-empty query).
  function hitRow(hit: SearchHit) {
    return (
      <HitRow
        key={`${hit.module}.${hit.name}`}
        icon={hit.icon}
        name={hit.name}
        importStmt={hit.importStmt}
        module={hit.module.replace("diagrams.", "")}
        onInsert={onInsert}
        onContextMenu={openMenu}
      />
    );
  }

  const isBlank = !query.trim();

  return (
    <div className="node-search" style={width !== undefined ? { width } : undefined}>
      <div className="search-input-wrap">
        <span className="search-icon" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.4" />
            <line x1="9.4" y1="9.4" x2="13" y2="13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
        </span>
        <input
          type="search"
          placeholder="Search nodes — EC2, Kafka..."
          aria-label="Search nodes"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          data-testid="node-search-input"
        />
      </div>
      {isBlank ? (
        <ul className="node-search-results node-tree">
          {tree.map((provider) => {
            const providerKey = `provider:${provider.provider}`;
            const providerOpen = expanded.has(providerKey);
            return (
              <li key={provider.provider} className="tree-node">
                <button
                  type="button"
                  className="tree-row tree-provider-row"
                  aria-expanded={providerOpen}
                  onClick={() => toggle(providerKey)}
                >
                  <Chevron />
                  <span className="tree-provider-name">{providerLabel(provider.provider)}</span>
                  <span className="tree-badge">{provider.count}</span>
                </button>
                {providerOpen && (
                  <ul className="tree-children">
                    {provider.categories.map((cat) => {
                      const categoryKey = `category:${cat.module}`;
                      const categoryOpen = expanded.has(categoryKey);
                      const label = cat.category || cat.module.split(".").pop() || cat.module;
                      return (
                        <li key={cat.module} className="tree-node">
                          <button
                            type="button"
                            className="tree-row tree-category-row"
                            aria-expanded={categoryOpen}
                            onClick={() => toggle(categoryKey)}
                          >
                            <Chevron />
                            <span className="tree-category-name">{label}</span>
                            <span className="tree-badge">{cat.classes.length}</span>
                          </button>
                          {categoryOpen && (
                            <ul className="tree-class-rows">
                              {cat.classes.map((cls) => (
                                <HitRow
                                  key={`${cat.module}.${cls.name}`}
                                  icon={cls.icon}
                                  name={cls.name}
                                  importStmt={`from ${cat.module} import ${cls.name}`}
                                  onInsert={onInsert}
                                  onContextMenu={openMenu}
                                  inTree
                                />
                              ))}
                            </ul>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <ul className="node-search-results">{hits.map((hit) => hitRow(hit))}</ul>
      )}
      {menu && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          hit={menu.hit}
          onInsert={onInsert}
          onClose={() => setMenu(null)}
        />
      )}
    </div>
  );
}
