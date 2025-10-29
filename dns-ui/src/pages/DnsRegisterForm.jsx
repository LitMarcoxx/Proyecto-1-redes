import { useState, useEffect } from "react";
import api from "../api";
import { useNavigate, useSearchParams } from "react-router-dom";

function DnsRegisterForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fqdnParam = searchParams.get("fqdn");

  const [formData, setFormData] = useState({
    fqdn: "",
    type: "",
    targets: [{ ip: "", weight: "" }],
  });

  useEffect(() => {
    if (fqdnParam) {
  fetch(api(`/api/records/${encodeURIComponent(fqdnParam)}`))
        .then((res) => res.json())
        .then((data) => {
          setFormData({
            fqdn: data.fqdn || "",
            type: data.type || "",
            targets:
              data.type === "weight"
                ? (data.targets || [{ ip: "", weight: "" }]).map((t) => ({ ip: t.ip || "", weight: t.weight?.toString() || "" }))
                : (data.targets || [{ ip: "" }]).map((t) => ({ ip: t.ip || "" }))
          });
        })
        .catch((err) =>
          console.error("Error al cargar datos del registro:", err)
        );
    }
  }, [fqdnParam]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleTargetChange = (index, field, value) => {
    setFormData((prev) => {
      const updatedTargets = [...prev.targets];
      updatedTargets[index] = {
        ...updatedTargets[index],
        [field]: value,
      };
      return { ...prev, targets: updatedTargets };
    });
  };

  const addTarget = () => {
    setFormData((prev) => ({
      ...prev,
      targets: [...prev.targets, formData.type === "weight" ? { ip: "", weight: "" } : { ip: "" }],
    }));
  };

  const removeTarget = (index) => {
    setFormData((prev) => ({
      ...prev,
      targets: prev.targets.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const method = fqdnParam ? "PUT" : "POST";
    const url = fqdnParam
      ? api(`/api/records/${encodeURIComponent(fqdnParam)}`)
      : api("/api/records");

    const recordData = {
      fqdn: formData.fqdn,
      type: formData.type,
      targets: formData.targets.map((t, i) => {
        const target = {
          id: `t${i + 1}`,
          ip: t.ip,
          geo_location: {
            country: "ZZ",
            region: "unknown",
          },
        };
        if (formData.type === "weight") {
          target.weight = t.weight ? parseInt(t.weight) : 1;
        }
        return target;
      }),
    };

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recordData),
      });

      if (response.ok) {
        alert("Registro guardado correctamente.");
        navigate("/");
      } else {
        alert("Error al guardar el registro.");
      }
    } catch (error) {
      console.error("Error al enviar el formulario:", error);
      alert("Error de conexión con el servidor.");
    }
  };

  const allowsMultipleIPs = ["multi", "geo", "weight", "roundtrip"].includes(
    formData.type
  );
  const isWeightType = formData.type === "weight";

  return (
    <div className="home-page">
      <header>
        <h1 style={{ marginBottom: "2.5rem" }}>DNS Register Form</h1>
      </header>

      <div className="register-list">
        <div
          className="register-form-container"
          style={{
            padding: "2rem 3rem",
            lineHeight: "2.3rem",
          }}
        >
          <form onSubmit={handleSubmit}>
            {/* DOMAIN */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: "1.2rem",
                gap: "1rem",
              }}
            >
              <label style={{ width: "180px", textAlign: "right" }}>
                Domain:
              </label>
              <input
                type="text"
                name="fqdn"
                value={formData.fqdn}
                onChange={handleChange}
                placeholder="example.com"
                style={{ flex: 1 }}
              />
            </div>

            {/* REGISTER TYPE */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: "1.2rem",
                gap: "1rem",
              }}
            >
              <label style={{ width: "180px", textAlign: "right" }}>
                Register type:
              </label>
              <select
                name="type"
                value={formData.type}
                onChange={handleChange}
                style={{ flex: 1 }}
              >
                <option value="">Select type</option>
                <option value="single">single</option>
                <option value="multi">multi</option>
                <option value="roundtrip">roundtrip</option>
                <option value="weight">weight</option>
                <option value="geo">geo</option>
              </select>
            </div>

            {/* TARGETS */}
            <div
              style={{
                display: "flex",
                alignItems: allowsMultipleIPs ? "flex-start" : "center",
                marginBottom: "1.8rem",
                gap: "1rem",
              }}
            >
              <label
                style={{
                  width: "180px",
                  textAlign: "right",
                  marginTop: allowsMultipleIPs ? "0.5rem" : "-0.6rem",
                }}
              >
                IP (depende del tipo):
              </label>
              <div style={{ flex: 1 }}>
                {formData.targets.map((target, index) => (
                  <div
                    key={index}
                    style={{
                      display: "flex",
                      gap: "0.7rem",
                      marginBottom: "0.7rem",
                    }}
                  >
                    <input
                      type="text"
                      value={target.ip}
                      placeholder="198.145.67.50"
                      onChange={(e) =>
                        handleTargetChange(index, "ip", e.target.value)
                      }
                      style={{ flex: 1 }}
                    />
                    {isWeightType && (
                      <input
                        type="number"
                        min="1"
                        value={target.weight}
                        placeholder="Peso"
                        onChange={(e) =>
                          handleTargetChange(index, "weight", e.target.value)
                        }
                        style={{ width: "80px" }}
                      />
                    )}
                    {allowsMultipleIPs && formData.targets.length > 1 && (
                      <button
                        type="button"
                        className="btn small"
                        onClick={() => removeTarget(index)}
                      >
                        -
                      </button>
                    )}
                  </div>
                ))}
                {allowsMultipleIPs && (
                  <button
                    type="button"
                    className="btn small"
                    style={{ marginTop: "0.5rem" }}
                    onClick={addTarget}
                  >
                    + Add
                  </button>
                )}
              </div>
            </div>

            {/* HEALTH CHECK */}
            {/* Health check section removed - only domain, type and IP remain */}

            {/* BUTTONS */}
            <div
              className="card-actions"
              style={{
                marginTop: "2rem",
                display: "flex",
                justifyContent: "center",
                gap: "1.2rem",
              }}
            >
              <button type="submit" className="btn">
                Save
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => navigate("/")}
              >
                Go back
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default DnsRegisterForm;
