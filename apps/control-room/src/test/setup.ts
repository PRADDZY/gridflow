import "@testing-library/jest-dom/vitest";

Object.defineProperty(HTMLMediaElement.prototype, "load", {
  configurable: true,
  value: () => {},
});

Object.defineProperty(HTMLMediaElement.prototype, "play", {
  configurable: true,
  value: () => Promise.resolve(),
});
