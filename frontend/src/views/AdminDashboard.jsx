import { useApi } from "../hooks/useApi";
import DataTable from "../components/shared/DataTable";

export default function AdminDashboard() {
  const { data: summary, loading: summaryLoading, error: summaryError } =
    useApi("/admin/platform-summary");
  const { data: vendors, loading: vendorsLoading, error: vendorsError } =
    useApi("/admin/vendors");

  const vendorColumns = [
    { key: "name", label: "Vendor Name" },
    { key: "slug", label: "Slug" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => (
        <span style={{ color: row.is_active ? "green" : "red" }}>
          {row.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Admin Dashboard</h1>

      {summaryError && <p style={{ color: "red" }}>Error: {summaryError}</p>}
      {summaryLoading && <p>Loading summary...</p>}

      {!summaryLoading && !summaryError && summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <StatCard label="Total Orders" value={summary.total_orders} />
          <StatCard label="Active Vendors" value={summary.active_vendors} />
        </div>
      )}

      <section>
        <h2>Vendors</h2>
        {vendorsError && <p style={{ color: "red" }}>Error: {vendorsError}</p>}
        {vendorsLoading ? (
          <p>Loading vendors...</p>
        ) : (
          <DataTable
            columns={vendorColumns}
            rows={vendors ?? []}
            emptyMessage="No vendors found"
          />
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
      <p style={{ margin: 0, color: "#666", fontSize: "0.9rem" }}>{label}</p>
      <p style={{ margin: "0.5rem 0 0", fontSize: "1.5rem", fontWeight: "bold" }}>{value}</p>
    </div>
  );
}
