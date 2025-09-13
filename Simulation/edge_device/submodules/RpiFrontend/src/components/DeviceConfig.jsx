import React, { useEffect, useState, useCallback } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const api_prefix = `http://${window.location.hostname}:8000/rpi`;

const DeviceConfig = () => {
  const navigate = useNavigate();
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [deviceBrands, setDeviceBrands] = useState([]);
  const [deviceModels, setDeviceModels] = useState([]);
  const [clientCodes, setClientCodes] = useState([]);
  const [selectedClientCodes, setSelectedClientCodes] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [projectCode, setProjectCode] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    control,
    formState: { errors },
  } = useForm({
    defaultValues: {
      pinouts: [],
    },
  });

  const {
    fields: pinoutFields,
    append: appendPinout,
    remove: removePinout,
  } = useFieldArray({
    control,
    name: "pinouts",
  });

  const deviceType = watch("deviceType");
  const deviceBrand = watch("deviceBrand");
  const commType = watch("comm_type");

  const handleRemoveDevice = (index) => {
    setDevices((prev) => prev.filter((_, i) => i !== index));
  };

  const fetchData = useCallback(async (url, setter) => {
    setLoading(true);
    try {
      const response = await axios.get(url);
      setter(response.data);
    } catch (error) {
      console.error(`Error fetching from ${url}:`, error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(`${api_prefix}/device-types`, (data) =>
      setDeviceTypes(data.device_types || [])
    );
    fetchData(`${api_prefix}/client-codes`, (data) =>
      setClientCodes(data.client_codes || [])
    );
  }, [fetchData]);

  useEffect(() => {
    if (deviceType) {
      fetchData(`${api_prefix}/device-brands/${deviceType}`, (data) =>
        setDeviceBrands(data.device_brands || [])
      );
    } else {
      setDeviceBrands([]);
    }
  }, [deviceType, fetchData]);

  useEffect(() => {
    if (deviceBrand && deviceType) {
      fetchData(
        `${api_prefix}/device-models/${deviceType}/${deviceBrand}`,
        (data) => setDeviceModels(data.device_models || [])
      );
    } else {
      setDeviceModels([]);
    }
  }, [deviceBrand, deviceType, fetchData]);

  const handleClientCodeChange = (code) => {
    setSelectedClientCodes((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const onAddDevice = (data) => {
    const newDevice = {
      device_type: data.deviceType,
      device_brand: data.deviceBrand,
      part_num: data.deviceModel,
      device_id: `${data.deviceType}:${data.deviceModel}:${data.deviceSerial}`,
      device_serial_no: data.deviceSerial,
      comm_type: data.comm_type,
    };

    if (data.comm_type !== "gpio") {
      newDevice.num_phases = data.num_phases;
      newDevice.phases = data.phases;
    }

    if (data.comm_type === "modbus-rtu") {
      newDevice.modbus_rtu_details = {
        part_num: data.rtu_part_num,
        port: data.rtu_port,
        stop_bits: data.rtu_stop_bits,
        parity: data.rtu_parity,
        baudrate: data.rtu_baudrate,
        slave_id: data.rtu_slave_id,
      };
    } else if (data.comm_type === "modbus-tcp") {
      newDevice.modbus_tcp_details = {
        IP: data.tcp_ip,
        port: data.tcp_port,
      };
    } else if (data.comm_type === "gpio") {
      const pinoutsObject = {};
      data.pinouts.forEach((pinout) => {
        pinoutsObject[pinout.name] = {
          pin_num: pinout.pin_num,
          type: pinout.type,
        };
      });

      newDevice.pinouts = pinoutsObject;
    }

    setDevices((prev) => [...prev, newDevice]);
    reset();
  };

  const onSubmit = async () => {
    if (devices.length === 0) {
      alert("No devices to submit!");
      return;
    }

    if (selectedClientCodes.length === 0) {
      alert("Please select at least one client code!");
      return;
    }

    if (!projectCode.trim()) {
      alert("Please enter a project code!");
      return;
    }

    const payload = {
      client_codes: selectedClientCodes,
      devices: devices,
      project_code: projectCode,
    };

    try {
      setLoading(true);
      await axios.post(`${api_prefix}/device-config`, payload);
      alert("Devices submitted successfully!");
      setDevices([]);
      setSelectedClientCodes([]);
      setProjectCode("");
    } catch (err) {
      console.error("Error submitting devices:", err);
      alert("Failed to submit devices. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-white shadow-lg rounded-xl p-6 mt-10">
      <h2 className="text-2xl font-semibold text-center mb-4">
        Device Configuration
      </h2>

      {loading && <p className="text-blue-500 text-center">Loading...</p>}

      <div className="mb-6">
        <label className="block text-gray-700 font-medium mb-2">
          Select Client Codes
        </label>
        <div className="flex flex-wrap gap-2">
          {clientCodes.map((code) => (
            <button
              type="button"
              key={code}
              onClick={() => handleClientCodeChange(code)}
              className={`px-3 py-1 rounded-full text-sm ${
                selectedClientCodes.includes(code)
                  ? "bg-green-500 text-white"
                  : "bg-gray-200 text-gray-700"
              }`}
            >
              {code}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <label className="block text-gray-700 font-medium mb-2">
          Project Code
        </label>
        <input
          type="text"
          value={projectCode}
          onChange={(e) => setProjectCode(e.target.value)}
          className="w-full p-2 border rounded-lg"
          placeholder="Enter project code"
          required
        />
      </div>

      <form onSubmit={handleSubmit(onAddDevice)} className="space-y-6">
        <div>
          <label className="block text-gray-700 font-medium mb-1">
            Device Type
          </label>
          <select
            {...register("deviceType", { required: "Device type is required" })}
            className="w-full p-2 border rounded-lg"
          >
            <option value="">Select Device Type</option>
            {deviceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          {errors.deviceType && (
            <p className="text-red-500 text-sm">{errors.deviceType.message}</p>
          )}
        </div>

        <div>
          <label className="block text-gray-700 font-medium mb-1">
            Device Brand
          </label>
          <select
            {...register("deviceBrand", {
              required: "Device brand is required",
            })}
            className="w-full p-2 border rounded-lg"
          >
            <option value="">Select Device Brand</option>
            {deviceBrands.map((brand) => (
              <option key={brand} value={brand}>
                {brand}
              </option>
            ))}
          </select>
          {errors.deviceBrand && (
            <p className="text-red-500 text-sm">{errors.deviceBrand.message}</p>
          )}
        </div>

        <div>
          <label className="block text-gray-700 font-medium mb-1">
            Device Model
          </label>
          <select
            {...register("deviceModel", {
              required: "Device model is required",
            })}
            className="w-full p-2 border rounded-lg"
          >
            <option value="">Select Device Model</option>
            {deviceModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
          {errors.deviceModel && (
            <p className="text-red-500 text-sm">{errors.deviceModel.message}</p>
          )}
        </div>

        <div>
          <label className="block text-gray-700 font-medium mb-1">
            Device Serial Number
          </label>
          <input
            type="text"
            {...register("deviceSerial", {
              required: "Device serial is required",
            })}
            className="w-full p-2 border rounded-lg"
          />
          {errors.deviceSerial && (
            <p className="text-red-500 text-sm">
              {errors.deviceSerial.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-gray-700 font-medium mb-1">
            Communication Type
          </label>
          <select
            {...register("comm_type", {
              required: "Communication type is required",
            })}
            className="w-full p-2 border rounded-lg"
          >
            <option value="">Select Communication Type</option>
            <option value="modbus-rtu">Modbus RTU</option>
            <option value="modbus-tcp">Modbus TCP</option>
            <option value="gpio">GPIO</option>
          </select>
          {errors.comm_type && (
            <p className="text-red-500 text-sm">{errors.comm_type.message}</p>
          )}
        </div>

        {commType !== "gpio" && (
          <div>
            <label className="block text-gray-700 font-medium mb-1">
              Number of Phases
            </label>
            <input
              type="number"
              {...register("num_phases")}
              className="w-full p-2 border rounded-lg"
            />
          </div>
        )}

        {commType !== "gpio" && (
          <div>
            <label className="block text-gray-700 font-medium mb-1">
              Phases (comma separated)
            </label>
            <input
              type="text"
              {...register("phases")}
              className="w-full p-2 border rounded-lg"
            />
          </div>
        )}

        {commType === "modbus-rtu" && (
          <div className="bg-gray-100 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Modbus RTU Details</h3>
            <input
              {...register("rtu_part_num")}
              placeholder="Part Number"
              className="w-full mb-2 p-2 border rounded"
            />
            <input
              {...register("rtu_port")}
              placeholder="Port"
              className="w-full mb-2 p-2 border rounded"
            />
            <input
              {...register("rtu_stop_bits")}
              placeholder="Stop Bits"
              className="w-full mb-2 p-2 border rounded"
            />
            <input
              {...register("rtu_parity")}
              placeholder="Parity"
              className="w-full mb-2 p-2 border rounded"
            />
            <input
              {...register("rtu_baudrate")}
              placeholder="Baudrate"
              className="w-full mb-2 p-2 border rounded"
            />
            <input
              {...register("rtu_slave_id")}
              placeholder="Slave ID"
              className="w-full mb-2 p-2 border rounded"
            />
          </div>
        )}

        {commType === "modbus-tcp" && (
          <div className="bg-gray-100 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Modbus TCP Details</h3>
            <input
              {...register("tcp_ip")}
              placeholder="IP Address"
              className="w-full mb-2 p-2 border rounded"
            />
            <input
              {...register("tcp_port")}
              placeholder="Port"
              className="w-full mb-2 p-2 border rounded"
            />
          </div>
        )}

        {commType === "gpio" && (
          <div className="bg-gray-100 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">GPIO Pinouts</h3>
            {pinoutFields.map((field, index) => (
              <div
                key={field.id}
                className="flex items-center gap-2 mb-2 w-full"
              >
                <input
                  {...register(`pinouts.${index}.name`, {
                    required: "Name required",
                  })}
                  placeholder="Name (e.g. OTI_alarm)"
                  className="flex-1 p-2 border rounded"
                />
                <input
                  {...register(`pinouts.${index}.pin_num`, {
                    required: "Address required",
                  })}
                  placeholder="Address (e.g. d1)"
                  className="flex-1 p-2 border rounded"
                />
                <input
                  {...register(`pinouts.${index}.type`, {
                    required: "Type required",
                  })}
                  placeholder="type (input/output)"
                  className="flex-1 p-2 border rounded"
                />
                <button
                  type="button"
                  onClick={() => removePinout(index)}
                  className="text-red-500 font-bold"
                >
                  X
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() => appendPinout({ name: "", pin_num: "", type: "" })}
              className="mt-2 px-4 py-1 bg-blue-500 text-white rounded"
            >
              + Add Pinout
            </button>
          </div>
        )}

        <div className="flex justify-between">
          <button
            type="submit"
            className="bg-blue-600 text-white w-1/3 mr-2 py-2 px-4 rounded-lg hover:bg-blue-700 transition"
          >
            Add Device
          </button>
          <button
            type="button"
            onClick={onSubmit}
            className={`font-bold w-1/3 mx-2 py-2 px-4 rounded-lg transition-all duration-300 ${
              devices.length === 0 ||
              selectedClientCodes.length === 0 ||
              !projectCode.trim()
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-green-600 text-white hover:bg-green-700"
            }`}
            disabled={
              devices.length === 0 ||
              selectedClientCodes.length === 0 ||
              !projectCode.trim()
            }
          >
            Submit
          </button>
          <button
            type="button"
            className="w-1/3 ml-2 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300"
            onClick={() => navigate("/")}
          >
            Home
          </button>
        </div>
      </form>

      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-2">Added Devices</h3>
        {devices.map((device, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="border rounded-lg p-4 mb-2 shadow-sm bg-gray-50 relative"
          >
            <pre className="text-sm">{JSON.stringify(device, null, 2)}</pre>
            <button
              type="button"
              onClick={() => handleRemoveDevice(index)}
              className="absolute top-2 right-2 text-red-500 font-bold"
            >
              X
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default DeviceConfig;
