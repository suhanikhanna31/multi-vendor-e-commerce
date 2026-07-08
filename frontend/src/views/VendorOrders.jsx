import { useApi } from "../hooks/useApi";
import DataTable from "../components/shared/DataTable";

export default function VendorOrders() {
  const vendorId = sessionStorage.getItem("vendor_id");

  const { data: orders, loading, error } = useApi(
    vendorId ? `/vendor/${vendorId}/orders` : null,
    { skip: !vendorId }
  );

  const columns = [
    { key: "external_order_id", label: "Order ID" },
    {
      key: "amount_inr",
      label: "Amount (₹)",
      render: (row) => `₹${Number(row.amount_inr).toLocaleString()}`,
    },
    { key: "status", label: "Status" },
    {
      key: "created_at",
      label: "Date",
      render: (row) => new Date(row.created_at).toLocaleDateString(),
    },
  ];

  if (!vendorId) {
    return (
      <div style={{ padding: "2rem" }}>
        <p style={{ color: "red" }}>No vendor account linked to this login.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem" }}>
      <h1>My Orders</h1>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {loading ? (
        <p>Loading orders...</p>
      ) : (
        <DataTable columns={columns} rows={orders ?? []} emptyMessage="No orders yet" />
      )}
    </div>
  );
}
