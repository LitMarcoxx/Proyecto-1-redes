import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import IpToCountry from "./pages/IpToCountry";
import IpToCountryForm from "./pages/IpToCountryForm.jsx";
import DnsRegisterForm from "./pages/DnsRegisterForm";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/ip-to-country" element={<IpToCountry />} />
      <Route path="/dns-form" element={<DnsRegisterForm />} />
      <Route path="/dns-form/:id" element={<DnsRegisterForm />} />
    </Routes>
  );
}

export default App;
