/**
 * Noah's Widgets
 * Export all your widgets here — the registry picks them up automatically.
 */
import { Widget } from '../../shared/widget-base.js';
import { CompressionWidget } from './compression-widget.js';

export class HelloWidget extends Widget {
  constructor() {
    super({
      id: 'noah:hello',
      name: 'Hello Widget',
      author: 'noah',
      description: 'Starter widget — replace me with something cool',
    });
  }

  render() {
    return `<div class="widget">👋 Noah's widget is live</div>`;
  }
}

export const widgets = [
  new HelloWidget(),
  new CompressionWidget(),
];
