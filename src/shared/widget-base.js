/**
 * Base class for all Rangers widgets.
 * Every widget must extend this and implement render().
 */
export class Widget {
  constructor({ id, name, author, description = '' }) {
    this.id = id;
    this.name = name;
    this.author = author;
    this.description = description;
    this.state = {};
  }

  /** Override to return HTML string or DOM element */
  render() {
    throw new Error(`${this.name}: render() not implemented`);
  }

  /** Override for periodic data refresh */
  async refresh() {}

  /** Override for cleanup */
  destroy() {}

  setState(partial) {
    this.state = { ...this.state, ...partial };
  }

  toJSON() {
    return {
      id: this.id,
      name: this.name,
      author: this.author,
      description: this.description,
    };
  }
}
