/**
 * Shared type definitions and constants for Rangers.
 *
 * @typedef {Object} WidgetConfig
 * @property {string} id - Unique widget identifier (author:name format)
 * @property {string} name - Display name
 * @property {string} author - Ranger who built it
 * @property {string} [description] - What it does
 *
 * @typedef {'small'|'medium'|'large'|'full'} WidgetSize
 */

export const RANGERS = ['noah', 'chase', 'josh'];

export const WIDGET_SIZES = {
  small: { cols: 1, rows: 1 },
  medium: { cols: 2, rows: 1 },
  large: { cols: 2, rows: 2 },
  full: { cols: 4, rows: 2 },
};
