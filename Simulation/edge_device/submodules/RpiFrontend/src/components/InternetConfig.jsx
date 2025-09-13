import { useForm, Controller } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const api_prefix = `http://${window.location.hostname}:8000/rpi`;

const InternetConfig = () => {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    control,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      connectionType: "wifi",
    },
  });

  const connectionType = watch("connectionType");

  const onSubmit = async (data) => {
    try {
      const payload = {
        connType: data.connectionType,
      };

      if (data.connectionType === "wifi") {
        payload.wifiSsid = data.wifiSsid;
        payload.wifiPassword = data.wifiPassword;
      } else if (data.connectionType === "ethernet") {
        payload.ipAddress = data.ipAddress;
        payload.subnetMask = data.subnetMask;
      } else if (data.connectionType === "cellular") {
        payload.carrier = data.carrier;
        payload.simNumber = data.simNumber;
      }

      const response = await axios.post(
        `${api_prefix}/internet-config`,
        payload
      );
      alert("Configuration submitted successfully!");
      console.log(response.data);
      reset();
    } catch (error) {
      alert("Error submitting configuration: " + error.message);
      console.error(error);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-blue-100 to-indigo-200">
      <form
        className="bg-white shadow-lg rounded-lg px-8 pt-6 pb-8 w-full max-w-md"
        onSubmit={handleSubmit(onSubmit)}
      >
        <h1 className="text-3xl font-semibold mb-6 text-center text-gray-800">
          Device Configuration
        </h1>

        <label className="block text-gray-700 font-medium mt-4">
          Connection Type:
        </label>
        <Controller
          control={control}
          name="connectionType"
          render={({ field }) => (
            <select
              {...field}
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400"
            >
              <option value="wifi">Wi-Fi</option>
              <option value="ethernet">Ethernet</option>
              <option value="cellular">Cellular</option>
            </select>
          )}
        />

        {connectionType === "wifi" && (
          <div className="mt-4">
            <label className="block text-gray-700 font-medium">
              Wi-Fi SSID:
            </label>
            <input
              {...register("wifiSsid", {
                required: "Wi-Fi SSID is required",
              })}
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-2 focus:ring-2 focus:ring-blue-400"
              placeholder="Enter Wi-Fi SSID"
            />
            {errors.wifiSsid && (
              <p className="text-red-500 text-sm">{errors.wifiSsid.message}</p>
            )}

            <label className="block text-gray-700 font-medium">
              Wi-Fi Password:
            </label>
            <input
              {...register("wifiPassword", {
                required: "Wi-Fi Password is required",
              })}
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-2 focus:ring-2 focus:ring-blue-400"
              placeholder="Enter Wi-Fi Password"
            />
            {errors.wifiPassword && (
              <p className="text-red-500 text-sm">
                {errors.wifiPassword.message}
              </p>
            )}
          </div>
        )}

        {connectionType === "ethernet" && (
          <div className="mt-4">
            <label className="block text-gray-700 font-medium">
              IP Address:
            </label>
            <input
              {...register("ipAddress", {
                required: "IP Address is required",
              })}
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-2 focus:ring-2 focus:ring-blue-400"
              placeholder="Enter IP Address"
            />
            {errors.ipAddress && (
              <p className="text-red-500 text-sm">{errors.ipAddress.message}</p>
            )}

            <label className="block text-gray-700 font-medium">
              Subnet Mask:
            </label>
            <input
              {...register("subnetMask", {
                required: "Subnet Mask is required",
              })}
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-2 focus:ring-2 focus:ring-blue-400"
              placeholder="Enter Subnet Mask"
            />
            {errors.subnetMask && (
              <p className="text-red-500 text-sm">
                {errors.subnetMask.message}
              </p>
            )}
          </div>
        )}

        {connectionType === "cellular" && (
          <div className="mt-4">
            <label className="block text-gray-700 font-medium">Carrier:</label>
            <input
              {...register("carrier", {
                required: "Carrier is required",
              })}
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-2 focus:ring-2 focus:ring-blue-400"
              placeholder="Enter Carrier Name"
            />
            {errors.carrier && (
              <p className="text-red-500 text-sm">{errors.carrier.message}</p>
            )}

            <label className="block text-gray-700 font-medium">
              SIM Number:
            </label>
            <input
              {...register("simNumber", {
                required: "SIM Number is required",
              })}
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-2 focus:ring-2 focus:ring-blue-400"
              placeholder="Enter SIM Number"
            />
            {errors.simNumber && (
              <p className="text-red-500 text-sm">{errors.simNumber.message}</p>
            )}
          </div>
        )}

        <div className="flex justify-between mt-6">
          <button
            type="submit"
            className="w-1/2 mr-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300"
          >
            Submit
          </button>
          <button
            type="button"
            className="w-1/2 ml-2 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300"
            onClick={() => navigate("/")}
          >
            Home
          </button>
        </div>
      </form>
    </div>
  );
};

export default InternetConfig;
