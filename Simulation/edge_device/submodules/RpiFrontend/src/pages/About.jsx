import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  FaUsers,
  FaBullseye,
  FaRocket,
  FaLinkedin,
  FaTwitter,
} from "react-icons/fa";

const teamMembers = [
  {
    name: "John Doe",
    role: "CEO & Founder",
    image: "https://randomuser.me/api/portraits/men/32.jpg",
    linkedin: "#",
    twitter: "#",
  },
  {
    name: "Jane Smith",
    role: "CTO",
    image: "https://randomuser.me/api/portraits/women/44.jpg",
    linkedin: "#",
    twitter: "#",
  },
  {
    name: "Alex Johnson",
    role: "Lead Developer",
    image: "https://randomuser.me/api/portraits/men/50.jpg",
    linkedin: "#",
    twitter: "#",
  },
];

const About = () => {
  const navigate = useNavigate();
  return (
    <div className="bg-gray-100">
      <section className="relative h-[60vh] bg-cover bg-center bg-[url('https://source.unsplash.com/1600x900/?technology,team')] flex items-center">
        <div className="bg-black/60 w-full h-full absolute top-0 left-0"></div>
        <div className="relative text-center text-white w-full">
          <motion.h1
            className="text-5xl font-bold"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
          >
            About Us
          </motion.h1>
          <p className="text-xl mt-4">
            Innovating the Future with Passion and Technology
          </p>
        </div>
      </section>

      <section className="max-w-5xl mx-auto py-16 px-6 text-center">
        <motion.h2
          className="text-3xl font-bold text-gray-800"
          initial={{ opacity: 0, y: -10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          Our Story
        </motion.h2>
        <p className="text-gray-600 mt-4 leading-relaxed">
          Founded in 2015, our company started as a small group of passionate
          engineers and designers working to build innovative solutions. Over
          the years, we have grown into a global tech leader with a mission to
          make a difference through technology.
        </p>
      </section>

      <section className="bg-white py-16">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12">
          <motion.div
            className="p-6 bg-blue-500 text-white rounded-lg shadow-lg flex flex-col items-center"
            whileHover={{ scale: 1.05 }}
          >
            <FaBullseye size={50} />
            <h3 className="text-2xl font-semibold mt-4">Our Mission</h3>
            <p className="mt-2 text-center">
              Empower businesses and individuals with cutting-edge technology
              that transforms lives.
            </p>
          </motion.div>

          <motion.div
            className="p-6 bg-indigo-500 text-white rounded-lg shadow-lg flex flex-col items-center"
            whileHover={{ scale: 1.05 }}
          >
            <FaRocket size={50} />
            <h3 className="text-2xl font-semibold mt-4">Our Vision</h3>
            <p className="mt-2 text-center">
              A world where technology seamlessly enhances human experiences and
              possibilities.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto py-16 px-6 text-center">
        <motion.h2
          className="text-3xl font-bold text-gray-800"
          initial={{ opacity: 0, y: -10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          Meet Our Team
        </motion.h2>
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8">
          {teamMembers.map((member, index) => (
            <motion.div
              key={index}
              className="bg-white shadow-lg rounded-lg p-6 text-center"
              whileHover={{ scale: 1.05 }}
            >
              <img
                src={member.image}
                alt={member.name}
                className="w-24 h-24 mx-auto rounded-full border-4 border-gray-300"
              />
              <h3 className="text-xl font-semibold mt-4">{member.name}</h3>
              <p className="text-gray-600">{member.role}</p>
              <div className="flex justify-center gap-4 mt-4">
                <a
                  href={member.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <FaLinkedin
                    size={24}
                    className="text-blue-600 hover:text-blue-800 transition"
                  />
                </a>
                <a
                  href={member.twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <FaTwitter
                    size={24}
                    className="text-blue-400 hover:text-blue-600 transition"
                  />
                </a>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="bg-blue-500 text-white py-16 text-center">
        <motion.h2
          className="text-3xl font-bold"
          initial={{ opacity: 0, y: -10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          Join Us on This Journey
        </motion.h2>
        <p className="mt-4 text-lg">
          Be part of our innovation. Let’s build the future together.
        </p>
        <button
          onClick={() => navigate("/contact")}
          className="mt-6 bg-white text-blue-500 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition"
        >
          Contact Us
        </button>
      </section>
    </div>
  );
};

export default About;
