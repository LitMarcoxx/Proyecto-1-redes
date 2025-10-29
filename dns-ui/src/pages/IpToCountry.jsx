import { useState, useEffect } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";

function IpToCountry() {
  const [ranges, setRanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ start_ip: "", end_ip: "", country: "" });
  const [isEdit, setIsEdit] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRanges = async () => {
      try {
  const res = await fetch(api("/api/ip_to_country?limit=100"));
        if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

        const json = await res.json();
        if (json && Array.isArray(json.data)) {
          setRanges(json.data);
        } else {
          setError("Formato de respuesta inesperado del servidor.");
        }
      } catch (err) {
        console.error("Error al obtener rangos:", err);
        setError("No se pudieron cargar los rangos desde la base de datos.");
      } finally {
        setLoading(false);
      }
    };

    fetchRanges();
  }, []);

  const openModal = (range = null) => {
    if (range) {
      setForm({
        start_ip: range.start_ip,
        end_ip: range.end_ip,
        country: range.country,
      });
      setIsEdit(true);
    } else {
      setForm({ start_ip: "", end_ip: "", country: "" });
      setIsEdit(false);
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = isEdit
        ? api(`/api/ip_to_country/${form.start_ip}`)
        : api("/api/ip_to_country");
      const method = isEdit ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

  const refreshed = await fetch(api("/api/ip_to_country?limit=100"));
      const json = await refreshed.json();
      setRanges(json.data || []);
      setShowModal(false);
    } catch (err) {
      console.error("Error guardando:", err);
      alert("No se pudo guardar el rango IP→País.");
    }
  };

  const handleDelete = async (start_ip) => {
    const confirmDelete = window.confirm(
      `¿Seguro que deseas eliminar el rango que inicia en ${start_ip}?`
    );
    if (!confirmDelete) return;

    try {
      const res = await fetch(
        api(`/api/ip_to_country/${encodeURIComponent(start_ip)}`),
        { method: "DELETE" }
      );

      if (res.ok) {
        setRanges((prev) => prev.filter((r) => r.start_ip !== start_ip));
      } else {
        alert("No se pudo eliminar el rango.");
      }
    } catch (err) {
      console.error("Error eliminando rango:", err);
      alert("Error de conexión al eliminar el rango.");
    }
  };

  return (
    <div className="home-page">
      <header>
        <h1>IP-to-Country</h1>
      </header>

      <div className="button-group">
        <button className="btn" onClick={() => openModal()}>
          Create new
        </button>
        <button className="btn" onClick={() => navigate("/")}>
          Go back
        </button>
      </div>

      <h3 className="subsection-title">Saved IPs</h3>

      {loading && <p style={{ color: "#8b949e" }}>Cargando rangos...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div className="register-list">
        {!loading && !error && ranges.length === 0 && (
          <p style={{ color: "#8b949e" }}>No hay rangos guardados.</p>
        )}

        {ranges.map((r, index) => (
          <div key={index} className="register-card">
            <div className="card-info">
              <p>
                <span className="label">Initial IP:</span> {r.start_ip}
              </p>
              <p>
                <span className="label">Final IP:</span> {r.end_ip}
              </p>
              <p>
                <span className="label">Country:</span> {r.country}
              </p>
            </div>

            <div className="card-actions">
              <button className="btn small" onClick={() => openModal(r)}>
                Edit
              </button>
              <button className="btn small" onClick={() => handleDelete(r.start_ip)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* --- Modal Popup --- */}
      {showModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: "#0d1117",
              padding: "2rem",
              borderRadius: "10px",
              width: "420px",
              boxShadow: "0 0 25px rgba(0,0,0,0.4)",
              border: "1px solid #30363d",
              color: "#c9d1d9",
            }}
          >
            <h2
              style={{
                marginBottom: "1.5rem",
                color: "white",
                fontWeight: "600",
                fontSize: "1.3rem",
                borderBottom: "1px solid #30363d",
                paddingBottom: "0.5rem",
                textAlign: "center",
              }}
            >
              {isEdit ? "Edit range" : "Create new range"}
            </h2>

            <form
              onSubmit={handleSubmit}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <div>
                <label
                  style={{
                    display: "block",
                    color: "#c9d1d9",
                    marginBottom: "0.3rem",
                    fontSize: "0.9rem",
                  }}
                >
                  Start IP
                </label>
                <input
                  type="text"
                  value={form.start_ip}
                  onChange={(e) => setForm({ ...form, start_ip: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "0.6rem",
                    borderRadius: "6px",
                    border: "1px solid #30363d",
                    backgroundColor: "#161b22",
                    color: "#c9d1d9",
                  }}
                  required
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    color: "#c9d1d9",
                    marginBottom: "0.3rem",
                    fontSize: "0.9rem",
                  }}
                >
                  End IP
                </label>
                <input
                  type="text"
                  value={form.end_ip}
                  onChange={(e) => setForm({ ...form, end_ip: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "0.6rem",
                    borderRadius: "6px",
                    border: "1px solid #30363d",
                    backgroundColor: "#161b22",
                    color: "#c9d1d9",
                  }}
                  required
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    color: "#c9d1d9",
                    marginBottom: "0.3rem",
                    fontSize: "0.9rem",
                  }}
                >
                  Country
                </label>
                <input
                  type="text"
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "0.6rem",
                    borderRadius: "6px",
                    border: "1px solid #30363d",
                    backgroundColor: "#161b22",
                    color: "#c9d1d9",
                  }}
                  required
                />
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: "0.75rem",
                  marginTop: "1.5rem",
                }}
              >
                <button
                  type="button"
                  className="btn small"
                  onClick={() => setShowModal(false)}
                  style={{
                    backgroundColor: "transparent",
                    color: "#c9d1d9",
                    border: "1px solid #30363d",
                    padding: "0.4rem 1rem",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn small"
                  style={{
                    backgroundColor: "#238636",
                    border: "none",
                    padding: "0.4rem 1rem",
                  }}
                >
                  {isEdit ? "Save" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default IpToCountry;
