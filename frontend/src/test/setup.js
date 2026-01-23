import '@testing-library/jest-dom';

// Mock localStorage for zustand persist middleware
const localStorageMock = {
    getItem: () => null,
    setItem: () => { },
    removeItem: () => { },
    clear: () => { },
};
global.localStorage = localStorageMock;
