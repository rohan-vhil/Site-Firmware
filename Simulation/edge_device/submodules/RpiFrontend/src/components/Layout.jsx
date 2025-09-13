import { useState } from "react";
import { Outlet, NavLink } from "react-router-dom";
import { Menu, X } from "lucide-react";

const Layout = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-100">
      <button
        className="md:hidden p-4 focus:outline-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      <div
        className={`absolute md:relative top-0 left-0 w-64 md:w-1/5 bg-white shadow-lg border-r border-gray-300 flex flex-col p-4 transition-transform duration-300 md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        } md:block h-full`}
      >
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">Menu</h2>
        <ul className="space-y-4">
          {["Home", "Devices", "About", "Contact"].map((item, index) => {
            const path = item.toLowerCase();
            return (
              <li key={index}>
                <NavLink
                  to={path === "home" ? "/" : `/${path}`}
                  end
                  className={({ isActive }) =>
                    `block px-4 py-2 text-lg font-medium rounded-lg transition-all duration-200 ease-in-out ${
                      isActive
                        ? "bg-gray-300 text-black font-bold border-l-4 border-blue-500"
                        : "text-gray-700 hover:bg-gray-200"
                    }`
                  }
                  onClick={() => setIsOpen(false)}
                >
                  {item}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="flex-1 h-full overflow-auto p-6 bg-gradient-to-r from-blue-100 to-purple-200">
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;
