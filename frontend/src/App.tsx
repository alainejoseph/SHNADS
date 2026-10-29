import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { DevicesPage } from './pages/DevicesPage';
import { LiveMonitorPage } from './pages/LiveMonitorPage';
import { FlowsPage } from './pages/FlowsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/devices" element={<DevicesPage />} />
          <Route path="/live" element={<LiveMonitorPage />} />
          <Route path="/flows" element={<FlowsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

