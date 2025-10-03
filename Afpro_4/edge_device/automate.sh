#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "🐘 Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

echo "🔧 Setting up PostgreSQL user password..."
# Switch to the postgres user and set the password
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"

echo "✅ PostgreSQL user password set."

echo "⚙️ Modifying pg_hba.conf for password authentication..."
# Set md5 authentication
PG_HBA="/etc/postgresql/$(ls /etc/postgresql)/main/pg_hba.conf"
sudo sed -i "s/^local\s*all\s*postgres\s*peer/local all postgres md5/" "$PG_HBA"

echo "🔄 Restarting PostgreSQL..."
sudo systemctl restart postgresql

echo "📂 Creating database 'raspberrypi'..."
sudo -u postgres psql -c "CREATE DATABASE raspberrypi;"

echo "✅ Database 'raspberrypi' created."

echo "🗄️ Creating two tables inside 'raspberrypi'..."
sudo -u postgres psql -d raspberrypi -c "
CREATE TABLE clientcodes (
	client_code_id serial PRIMARY KEY,
	client_code varchar(255) NOT NULL
);

CREATE TABLE masterdevices (
	master_device_id serial PRIMARY KEY,
	device_type varchar(255) NOT NULL,
	device_brand varchar(255) NOT NULL,
	device_model_no varchar(255) NOT NULL,
	device_specifications jsonb NOT NULL,
	device_modbus_addresses jsonb NOT NULL,
	device_fault_codes jsonb NOT NULL,
	CONSTRAINT unique_device_entry UNIQUE (device_type, device_brand, device_model_no)
);
"

echo "✅ Tables 'clientcodes' and 'masterdevices' created."

echo "🐍 Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-venv build-essential libpq-dev gcc


echo "🎉 All done! PostgreSQL is ready with your database and tables."
