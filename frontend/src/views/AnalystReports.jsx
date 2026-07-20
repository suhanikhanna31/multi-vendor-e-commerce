import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

function getToken() {
  return sessionStorage.getItem("access_token");
}

export default function AnalystReports() {
  const [vendorId, setVendorId] = useState("");
  const [etlStatus, setEtlStatus] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const runEtl = async () => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/analyst/etl/run`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error("ETL run failed");
      const data = await res.json();
      setEtlStatus(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const downloadDeck = async () => {
    if (!vendorId) {
      setError("Enter a vendor ID first");
      return;
    }
    setError(null);
    setDownloading(true);
    try {
      const res = await fetch(`${API_BASE}/analyst/reports/${vendorId}/deck`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error("Report generation failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `vendor-${vendorId}-report.pptx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Analyst Reports</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <section style={{ marginBottom: "2rem" }}>
        <h2>Run Weekly ETL</h2>
        <button onClick={runEtl}>Run ETL</button>
        {etlStatus && (
          <p>
            Processed {etlStatus.rows} rows across {etlStatus.vendors} vendors.
          </p>
        )}
      </section>

      <section>
        <h2>Generate Vendor Report Deck</h2>
        <input
          type="number"
          placeholder="Vendor ID"
          value={vendorId}
          onChange={(e) => setVendorId(e.target.value)}
          style={{ marginRight: "0.5rem", padding: "0.4rem" }}
        />
        <button onClick={downloadDeck} disabled={downloading}>
          {downloading ? "Generating..." : "Download Deck"}
        </button>
      </section>
    </div>
  );
}
