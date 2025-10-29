import { useState, useEffect } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";

function getRecordStatus(record) {
  if (!record.health || typeof record.health !== "object") return "—";

  const statuses = Object.entries(record.health)
    .map(([key, val]) => val?.status?.toLowerCase())
    .filter((s) => s === "healthy" || s === "unhealthy");

  if (statuses.length === 0) return "—";

  let healthyCount = 0;
  let unhealthyCount = 0;

  statuses.forEach((s) => {
    if (s === "healthy") healthyCount++;
    else if (s === "unhealthy") unhealthyCount++;
  });

  if (healthyCount === 0 && unhealthyCount === 0) return "—";
  if (healthyCount === unhealthyCount) return "—";
  if (healthyCount > unhealthyCount) return "healthy";
  return "unhealthy";
}

function Home() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        const response = await fetch(api("/api/records"));
        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        let recordsArray = [];
        if (Array.isArray(data)) {
          recordsArray = data;
        } else if (data && typeof data === "object") {
          recordsArray = Object.keys(data).map((k) => ({ fqdn: k, ...(data[k] || {}) }));
        }

        const processed = recordsArray.map((record) => ({
          ...record,
          status: getRecordStatus(record),
        }));

        setRecords(processed);
      } catch (err) {
        console.error("Error al obtener los registros:", err);
        setError("No se pudieron cargar los registros desde la base de datos.");
      } finally {
        setLoading(false);
      }
    };

    fetchRecords();

    const interval = setInterval(fetchRecords, 5000); // Actualización cada 5 segundos

    return () => clearInterval(interval); // Limpiar intervalo al desmontar
  }, []);

  const handleDelete = async (fqdn) => {
    const confirmDelete = window.confirm(
      `¿Seguro que deseas eliminar el registro "${fqdn}"?`
    );
    if (!confirmDelete) return;

    try {
      const response = await fetch(
        api(`/api/records/${encodeURIComponent(fqdn)}`),
        { method: "DELETE" }
      );

      if (response.ok) {
        setRecords((prev) => prev.filter((r) => r.fqdn !== fqdn));
      } else {
        alert("No se pudo eliminar el registro.");
      }
    } catch (err) {
      console.error("Error de conexión al eliminar:", err);
      alert("Error de conexión al eliminar el registro.");
    }
  };

  return (
    <div className="home-page">
      <header>
        <h1>DNS Registers</h1>
      </header>

      <div className="button-group">
        <button className="btn" onClick={() => navigate("/dns-form")}>
          Create new register
        </button>
        <button className="btn" onClick={() => navigate("/ip-to-country")}>
          IP-to-Country
        </button>
      </div>

      <h3 className="subsection-title">Saved Registers</h3>

      {loading && <p style={{ color: "#8b949e" }}>Cargando registros...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div className="register-list">
        {!loading && !error && records.length === 0 && (
          <p style={{ color: "#8b949e" }}>No hay registros guardados.</p>
        )}

        {records.map((record, index) => (
          <div key={index} className="register-card">
            <div className="card-info">
              <p>
                <span className="label">Domain:</span>{" "}
                {record.fqdn || record.domain || "—"}
              </p>
              <p>
                <span className="label">Register type:</span>{" "}
                {record.type || "—"}
              </p>
              {record.status && record.status !== "—" && (
                <p>
                  <span className="label">State:</span>{" "}
                  <span
                    style={{
                      color:
                        record.status === "healthy"
                          ? "#4ade80"
                          : "#f87171",
                      fontWeight: "500",
                    }}
                  >
                    {record.status}
                  </span>
                </p>
              )}
              {/* Mostrar los targets y debajo sus health checkers */}
              {Array.isArray(record.targets) && record.targets.length > 0 && (
                <div>
                  <h4>Targets:</h4>
                  {record.targets.map((target, tIdx) => {
                    // Buscar health por id del target
                    const health = record.health?.[target.id] || null;
                    return (
                      <div key={tIdx} style={{ marginBottom: "1.5rem", paddingLeft: "1rem", borderLeft: "2px solid #eee" }}>
                        <p>
                          <span className="label">IP:</span> {target.ip}
                          {record.type === "weight" && (
                            <span style={{ marginLeft: "1.2rem" }}>
                              <span className="label">Peso:</span> {target.weight ?? "—"}
                            </span>
                          )}
                        </p>
                        {target.geo_location && (
                          <p>
                            <span className="label">Geo:</span> {target.geo_location.country} ({target.geo_location.region})
                          </p>
                        )}
                        {health ? (
                          <div>
                            <h5 style={{ margin: "0.5rem 0 0.2rem 0" }}>Health Check:</h5>
                            {health.status_by_region && (
                              <div>
                                {Object.entries(health.status_by_region).map(([region, status]) => (
                                  <p key={region}>
                                    <span className="label">Region:</span> {region} | <span className="label">Status:</span> {status}
                                  </p>
                                ))}
                              </div>
                            )}
                            {health.rtt && health.rtt.by_region && (
                              <div>
                                {Object.entries(health.rtt.by_region).map(([region, rtt]) => (
                                  <p key={region}>
                                    <span className="label">Ping:</span> {region}: {rtt} ms
                                  </p>
                                ))}
                              </div>
                            )}
                            <p>
                              <span className="label">Último ping:</span> {health.rtt?.last_ms || "—"} ms
                            </p>
                            <p>
                              <span className="label">Status global:</span> {health.status || "—"}
                            </p>
                          </div>
                        ) : (
                          <p style={{ color: "#8b949e" }}>Sin health check para este target.</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="card-actions">
              <button
                className="btn small"
                onClick={() => navigate(`/dns-form?fqdn=${record.fqdn}`)}
              >
                Edit
              </button>
              <button
                className="btn small"
                onClick={() => handleDelete(record.fqdn)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Home;
