CREATE DATABASE IF NOT EXISTS gymkhana
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE gymkhana;

CREATE TABLE IF NOT EXISTS registrations (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(80) NOT NULL,
  email VARCHAR(254) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  plan VARCHAR(30) NOT NULL,
  start_date DATE NULL,
  preferred_time VARCHAR(20) NOT NULL,
  goals VARCHAR(500) NULL,
  consent BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_registrations_created_at (created_at),
  INDEX idx_registrations_email (email)
) ENGINE=InnoDB;
