import '@testing-library/jest-dom';
import { TextDecoder, TextEncoder } from 'util';

// Mock para fetch API
global.fetch = jest.fn();

// Mock para TextEncoder/TextDecoder
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

// Silenciar avisos do React
const originalConsoleError = console.error;
console.error = (...args: any[]) => {
  if (/Warning.*not wrapped in act/.test(args[0])) {
    return;
  }
  originalConsoleError(...args);
}; 