import { BrowserRouter, Route, Routes } from "react-router";
import Layout from "./Layout";
import Home from "../pages/Home";
import About from "../pages/About";
import Contact from "../pages/Contact";
import Devices from "../pages/Devices";
import Internet from "../pages/Internet";
import InstalledDevices from "../pages/InstalledDevices";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="contact" element={<Contact />} />
          <Route path="device-config" element={<Devices />} />
          <Route path="internet-config" element={<Internet />} />
          <Route path="devices" element={<InstalledDevices />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
