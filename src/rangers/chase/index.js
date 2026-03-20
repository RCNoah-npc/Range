/**
 * Chase's Widgets
 * Export all your widgets here — the registry picks them up automatically.
 */
import { Widget } from '../../shared/widget-base.js';

export class HelloWidget extends Widget {
  constructor() {
    super({
      id: 'chase:hello',
      name: 'Hello Widget',
      author: 'chase',
      description: 'Starter widget — replace me with something cool',
    });
  }

  render() {
    return `<div class="widget">👋 Chase's widget is live</div>`;
  }
}

export const widgets = [new HelloWidget()];
