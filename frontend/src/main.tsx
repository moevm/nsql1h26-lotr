import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';

async function enableMocking() {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }
  const { worker } = await import('./mocks/browser');
  return worker.start();
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
  },
});

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>
  );
});

// ReactDOM.createRoot(document.getElementById('root')!).render(
//   <React.StrictMode>
//     <QueryClientProvider client={queryClient}>
//        <App />
//     </QueryClientProvider>
//   </React.StrictMode>
// );
