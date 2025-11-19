import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

// Create a custom dark theme with LaunchDarkly colors
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#405BFF',
    },
    secondary: {
      main: '#00CCBB',
    },
    background: {
      default: '#0E0E1A',
      paper: '#1E1E2E',
    },
  },
  typography: {
    fontFamily: "'Roboto', sans-serif",
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
