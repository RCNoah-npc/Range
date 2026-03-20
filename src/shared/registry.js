/**
 * Widget Registry — auto-discovers and manages widgets from all rangers.
 * Each ranger exports widgets from their folder's index.js.
 */
const widgets = new Map();

export function register(widget) {
  if (widgets.has(widget.id)) {
    console.warn(`Widget "${widget.id}" already registered, skipping.`);
    return;
  }
  widgets.set(widget.id, widget);
}

export function get(id) {
  return widgets.get(id);
}

export function list() {
  return Array.from(widgets.values()).map((w) => w.toJSON());
}

export function listByAuthor(author) {
  return list().filter((w) => w.author === author);
}

export function remove(id) {
  const widget = widgets.get(id);
  if (widget) {
    widget.destroy();
    widgets.delete(id);
  }
}

export function clear() {
  widgets.forEach((w) => w.destroy());
  widgets.clear();
}
