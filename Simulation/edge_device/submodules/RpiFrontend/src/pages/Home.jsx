import React from "react";
import { useNavigate } from "react-router";

const Home = () => {
  const navigate = useNavigate();
  return (
    <div className="flex justify-center items-center h-full bg-gradient-to-r from-blue-100 to-purple-200">
      <div className="text-center bg-white shadow-lg rounded-lg p-10">
        <h1 className="text-4xl font-extrabold text-gray-800 mb-6">
          Site Management
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Manage your devices and internet settings with ease.
        </p>

        <div className="space-y-4">
          <button
            onClick={() => navigate("/internet-config")}
            className="w-full py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-700 transition duration-300"
          >
            Internet Settings
          </button>
          <button
            onClick={() => navigate("/device-config")}
            className="w-full py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-700 transition duration-300"
          >
            Manage Devices
          </button>
        </div>
      </div>
    </div>
  );
};

export default Home;
