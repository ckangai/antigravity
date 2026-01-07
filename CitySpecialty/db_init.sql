-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS city_specialty_db;

-- Select the database
USE city_specialty_db;

-- Create the table
CREATE TABLE IF NOT EXISTS city_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(255) NOT NULL,
    specialty TEXT NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
