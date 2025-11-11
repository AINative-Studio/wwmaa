// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'
import { toHaveNoViolations } from 'jest-axe'

// Add jest-axe matchers for accessibility testing
expect.extend(toHaveNoViolations)

// Mock react-markdown to avoid ES module issues
jest.mock('react-markdown', () => {
  return function ReactMarkdown({ children }) {
    return children;
  };
});

// Mock react-syntax-highlighter
jest.mock('react-syntax-highlighter', () => ({
  Prism: function SyntaxHighlighter({ children }) {
    return children;
  },
}));

jest.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  oneDark: {},
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
}

// Mock HTMLCanvasElement for axe-core
HTMLCanvasElement.prototype.getContext = jest.fn(() => {
  return {
    fillStyle: '',
    fillRect: jest.fn(),
    clearRect: jest.fn(),
    getImageData: jest.fn(() => ({
      data: [],
    })),
    putImageData: jest.fn(),
    createImageData: jest.fn(() => []),
    setTransform: jest.fn(),
    drawImage: jest.fn(),
    save: jest.fn(),
    restore: jest.fn(),
    beginPath: jest.fn(),
    moveTo: jest.fn(),
    lineTo: jest.fn(),
    closePath: jest.fn(),
    stroke: jest.fn(),
    translate: jest.fn(),
    scale: jest.fn(),
    rotate: jest.fn(),
    arc: jest.fn(),
    fill: jest.fn(),
    measureText: jest.fn(() => ({ width: 0 })),
    transform: jest.fn(),
    rect: jest.fn(),
    clip: jest.fn(),
  }
})

// Suppress console errors in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Not implemented: HTMLFormElement.prototype.submit'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})
