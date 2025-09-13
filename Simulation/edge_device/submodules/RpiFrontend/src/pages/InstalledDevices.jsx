import React, { useEffect, useState } from "react";
import axios from "axios";

const api_prefix = `http://${window.location.hostname}:8000/rpi`;

const InstalledDevices = () => {
  const [devices, setDevices] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get(`${api_prefix}/installed-devices`)
      .then((response) => {
        setDevices(response.data.devices);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleChange = (path, value) => {
    setDevices((prev) => {
      const updated = JSON.parse(JSON.stringify(prev));
      const keys = path.split(".");
      let obj = updated;

      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return updated;
    });
  };

  const handleDelete = (index) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this device?"
    );
    if (!confirmDelete) return;

    setDevices((prev) => {
      const updatedDevices = { ...prev };
      updatedDevices.device_list = [...updatedDevices.device_list];
      updatedDevices.device_list.splice(index, 1);
      updatedDevices.number_of_devices = updatedDevices.device_list.length;
      return updatedDevices;
    });
  };

  const handleSubmit = () => {
    axios
      .post(`${api_prefix}/update-installer-cfg`, devices)
      .then((response) => {
        alert("Device configuration updated successfully!");
      })
      .catch((err) => {
        alert("Error submitting device configuration.");
        console.error(err);
      });
  };

  if (loading)
    return <div className="text-center text-gray-500">Loading...</div>;
  if (error)
    return <div className="text-center text-red-500">Error: {error}</div>;

  return (
    <div className="max-w-7xl mx-auto p-4 bg-gradient-to-r from-blue-100 to-purple-200 min-h-screen">
      <h1 className="text-4xl font-bold mb-10 text-center text-blue-600">
        Edit Site Device Configuration
      </h1>

      <div className="bg-white rounded-xl shadow-md p-6 mb-10">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">
          Site Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-gray-600 text-sm">
          {Object.entries(devices).map(([key, value]) => {
            if (Array.isArray(value)) return null;
            return (
              <div key={key}>
                <label className="font-medium capitalize">
                  {key.replace(/_/g, " ")}:
                </label>
                <input
                  type="text"
                  value={value}
                  onChange={(e) => handleChange(`${key}`, e.target.value)}
                  className="block mt-1 w-full p-2 border rounded"
                />
              </div>
            );
          })}
        </div>
      </div>

      <h2 className="text-2xl font-semibold mb-6 text-gray-700">Devices</h2>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {devices.device_list.map((device, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-md p-6 flex flex-col justify-between relative"
          >
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Device {index + 1}
              </h3>

              {[
                "device_type",
                "device_brand",
                "part_num",
                "device_id",
                "device_serial_no",
                "comm_type",
                "num_phases",
                "phases",
              ].map((field) => (
                <div className="mb-3" key={field}>
                  <label className="block text-sm font-medium text-gray-700 capitalize">
                    {field.replace(/_/g, " ")}:
                  </label>
                  <input
                    type="text"
                    value={device[field]}
                    onChange={(e) =>
                      handleChange(
                        `device_list.${index}.${field}`,
                        e.target.value
                      )
                    }
                    className="w-full p-2 border rounded"
                  />
                </div>
              ))}

              {device.comm_type === "modbus-rtu" && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Modbus RTU Details
                  </h4>
                  {Object.entries(device.modbus_rtu_details || {}).map(
                    ([key, value]) => (
                      <div className="mb-2" key={key}>
                        <label className="block text-xs text-gray-600 capitalize">
                          {key.replace(/_/g, " ")}:
                        </label>
                        <input
                          type="text"
                          value={value}
                          onChange={(e) =>
                            handleChange(
                              `device_list.${index}.modbus_rtu_details.${key}`,
                              e.target.value
                            )
                          }
                          className="w-full p-2 border rounded text-sm"
                        />
                      </div>
                    )
                  )}
                </div>
              )}

              {device.comm_type === "modbus-tcp" && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Modbus TCP Details
                  </h4>
                  {Object.entries(device.modbus_tcp_details || {}).map(
                    ([key, value]) => (
                      <div className="mb-2" key={key}>
                        <label className="block text-xs text-gray-600 capitalize">
                          {key.replace(/_/g, " ")}:
                        </label>
                        <input
                          type="text"
                          value={value}
                          onChange={(e) =>
                            handleChange(
                              `device_list.${index}.modbus_tcp_details.${key}`,
                              e.target.value
                            )
                          }
                          className="w-full p-2 border rounded text-sm"
                        />
                      </div>
                    )
                  )}
                </div>
              )}

              {device.comm_type === "gpio" && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    GPIO Pinouts
                  </h4>
                  {Object.entries(device.pinouts || {}).map(
                    ([label, details]) => (
                      <div key={label} className="mb-4">
                        <label className="block text-xs text-gray-600">
                          {label}:
                        </label>
                        {Object.entries(details).map(([key, value]) => (
                          <div key={key} className="mb-1">
                            <label className="block text-xs text-gray-500 capitalize">
                              {key.replace(/_/g, " ")}:
                            </label>
                            <input
                              type="text"
                              value={value}
                              onChange={(e) =>
                                handleChange(
                                  `device_list.${index}.pinouts.${label}.${key}`,
                                  e.target.value
                                )
                              }
                              className="w-full p-2 border rounded text-sm"
                            />
                          </div>
                        ))}
                      </div>
                    )
                  )}
                </div>
              )}
            </div>

            {/* Delete Button */}
            <div className="mt-4">
              <button
                onClick={() => handleDelete(index)}
                className="w-full py-2 bg-red-500 text-white text-sm font-semibold rounded hover:bg-red-600 transition"
              >
                Delete Device
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 flex justify-center">
        <button
          onClick={handleSubmit}
          className="px-8 py-3 bg-green-500 text-white text-lg font-semibold rounded hover:bg-green-600 transition"
        >
          Submit All Changes
        </button>
      </div>
    </div>
  );
};

export default InstalledDevices;
