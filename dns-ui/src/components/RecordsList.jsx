import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function RecordsList() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("/api/registers");
        if (!res.ok) throw new Error("Error al obtener registros");
        const data = await res.json();
        setRecords(data);
      } catch (e) {
        setRecords([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleEdit = (id) => {
    navigate(`/register/${id}`);
  };

  if (loading) return <p>Cargando...</p>;

  return (
    <div className="tu-clase-lista">
      <h2>Registros DNS</h2>
      <table>
        <thead>
          <tr>
            <th>Dominio</th>
            <th>Tipo</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <tr key={r.id}>
              <td>{r.domain}</td>
              <td>{r.type}</td>
              <td>{r.state}</td>
              <td>
                <button onClick={() => handleEdit(r.id)}>Edit</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
