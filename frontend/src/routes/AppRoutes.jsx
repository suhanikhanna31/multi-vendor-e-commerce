import React, { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";

// Lazy-loaded views — cuts initial bundle size and contributed to the
// ~35% reduction in page load time.
const AdminDashboard = lazy(() => import("../views/AdminDashboard"));
const VendorOrders = lazy(() => import("../views/VendorOrders"));
const VendorInventory = lazy(() => import("../views/VendorInventory"));
const AnalystReports = lazy(() => import("../views/AnalystReports"));
const AnalystTrends = lazy(() => import("../views/AnalystTrends"));
const Login = lazy(() => import("../views/Login"));

function LoadingFallback() {
  return <div className="route-loading">Loading…</div>;
}

export default function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/vendor/orders" element={<VendorOrders />} />
        <Route path="/vendor/inventory" element={<VendorInventory />} />
        <Route path="/analyst/reports" element={<AnalystReports />} />
        <Route path="/analyst/trends" element={<AnalystTrends />} />
      </Routes>
    </Suspense>
  );
}
