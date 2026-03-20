/**
 * Ranger Loader — imports all ranger modules and registers their widgets.
 * Add new rangers here when they join.
 */
import { register } from '../shared/registry.js';

import { widgets as noahWidgets } from './noah/index.js';
import { widgets as chaseWidgets } from './chase/index.js';
import { widgets as joshWidgets } from './josh/index.js';

const allRangerWidgets = [
  ...noahWidgets,
  ...chaseWidgets,
  ...joshWidgets,
];

export function loadAll() {
  allRangerWidgets.forEach((widget) => register(widget));
  console.log(`Loaded ${allRangerWidgets.length} widgets from ${3} rangers`);
}
