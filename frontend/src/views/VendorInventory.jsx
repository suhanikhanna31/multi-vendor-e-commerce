export default function VendorInventory() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1>Inventory</h1>
      <p style={{ color: "#666" }}>
        Inventory management isn't built on the backend yet — there's no
        <code> /api/vendor/&lt;vendor_id&gt;/inventory</code> route defined.
        This page is a placeholder until that endpoint and its underlying
        model exist.
      </p>
    </div>
  );
}
