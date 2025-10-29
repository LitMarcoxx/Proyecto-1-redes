import { useState, useEffect } from "react";
import api from "../api";
import { useNavigate, useSearchParams } from "react-router-dom";

function IpToCountryForm() {
  const [form, setForm] = useState({
    initial_ip: "",
    final_ip: "",
    country: "",
    iso_code: "",
  });
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const id = searchParams.get("id");
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  useEffect(() => {
    if (isEdit) {
      const fetchRange = async () => {
        try {
      const res = await fetch(api(`/api/ip_to_country/${id}`));
          if (res.ok) {
            const data = await res.json();
            setForm({
              initial_ip: data.initial_ip || "",
              final_ip: data.final_ip || "",
              country: data.country || "",
              iso_code: data.iso_code || "",
            });
          }
        } catch (err) {
          console.error("Error cargando el rango:", err);
        }
      };
      fetchRange();
    }
  }, [id, isEdit]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const method = isEdit ? "PUT" : "POST";
      const url = isEdit
        ? api(`/api/ip_to_country/${id}`)
        : api("/api/ip_to_country");
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        navigate("/ip-to-country");
      } else {
        alert("Error al guardar el rango IP→País.");
      }
    } catch (err) {
      console.error("Error guardando:", err);
      alert("Error de conexión al guardar.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <header>
        <h1>{isEdit ? "Edit IP-to-Country" : "Create new IP-to-Country"}</h1>
      </header>

      <form className="register-form" onSubmit={handleSubmit}>
        <label>Initial IP</label>
        <input
          type="text"
          value={form.initial_ip}
          onChange={(e) => setForm({ ...form, initial_ip: e.target.value })}
          required
        />

        <label>Final IP</label>
        <input
          type="text"
          value={form.final_ip}
          onChange={(e) => setForm({ ...form, final_ip: e.target.value })}
          required
        />

        <label>Country</label>
        <input
          type="text"
          value={form.country}
          onChange={(e) => setForm({ ...form, country: e.target.value })}
          required
        />

        <label>ISO Code</label>
        <input
          type="text"
          value={form.iso_code}
          onChange={(e) => setForm({ ...form, iso_code: e.target.value })}
          required
        />

        <div className="button-group">
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Saving..." : isEdit ? "Save" : "Create"}
          </button>
          <button className="btn" type="button" onClick={() => navigate("/ip-to-country")}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default IpToCountryForm;
