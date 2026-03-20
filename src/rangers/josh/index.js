/**
 * Josh's Widgets
 * Export all your widgets here — the registry picks them up automatically.
 */
import { Widget } from '../../shared/widget-base.js';

export class HelloWidget extends Widget {
  constructor() {
    super({
      id: 'josh:hello',
      name: 'Hello Widget',
      author: 'josh',
      description: 'Starter widget — replace me with something cool',
    });
  }

  render() {
    return `<div class="widget">👋 Josh's widget is live</div>`;
  }
}

export const widgets = [new HelloWidget()];
