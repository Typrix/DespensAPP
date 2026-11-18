-- ========================================================
-- Script de Creación de Base de Datos - DespensAPP
-- Motor: MySQL 5.7+ / 8.0+ / MariaDB
-- Codificación: utf8mb4 / utf8mb4_unicode_ci
-- ========================================================

CREATE DATABASE IF NOT EXISTS `despensapp_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `despensapp_db`;

-- --------------------------------------------------------
-- 1. Tabla de Usuarios
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `avatar_initials` VARCHAR(4) DEFAULT 'US',
    `is_pro` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 2. Tabla de Listas de Compras
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `shopping_lists` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `icon_name` VARCHAR(50) DEFAULT 'clipboard-text-outline',
    `icon_color` VARCHAR(25) DEFAULT '#286ED3',
    `supermarket` VARCHAR(80) DEFAULT '',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_shopping_lists_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 3. Tabla de Artículos del Carrito de Compras
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `cart_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `list_id` INT NULL,
    `title` VARCHAR(150) NOT NULL,
    `subtitle` VARCHAR(100) DEFAULT 'Lista general',
    `price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `quantity` INT NOT NULL DEFAULT 1,
    `is_checked` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cart_items_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_cart_items_list`
        FOREIGN KEY (`list_id`) REFERENCES `shopping_lists` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 4. Tabla de Artículos de la Despensa
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pantry_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `name` VARCHAR(150) NOT NULL,
    `quantity` DECIMAL(10, 2) NOT NULL DEFAULT 1.00,
    `unit` VARCHAR(30) DEFAULT 'un.',
    `min_threshold` DECIMAL(10, 2) NOT NULL DEFAULT 2.00,
    `category` VARCHAR(50) DEFAULT 'General',
    `expiration_date` VARCHAR(20) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_pantry_items_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5. Tabla de Artículos de Listas de Compras (Estilo Supermercado)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `shopping_list_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `list_id` INT NOT NULL,
    `name` VARCHAR(150) NOT NULL,
    `price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `quantity` INT NOT NULL DEFAULT 1,
    `is_checked` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_shopping_list_items_list`
        FOREIGN KEY (`list_id`) REFERENCES `shopping_lists` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5b. Historial de Compras Finalizadas (gasto por semana, mes y año)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `purchase_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `list_id` INT NULL,
    `list_name` VARCHAR(100) NULL,
    `title` VARCHAR(150) NOT NULL,
    `price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `quantity` DECIMAL(10, 2) NOT NULL DEFAULT 1.00,
    `unit` VARCHAR(30) DEFAULT 'un.',
    `purchased_at` DATETIME NOT NULL,
    INDEX `idx_purchase_user_date` (`user_id`, `purchased_at`),
    CONSTRAINT `fk_purchase_history_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5. Tabla de Sesiones de la App (Telemetría)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `app_sessions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `platform` VARCHAR(50) DEFAULT 'Windows',
    `app_version` VARCHAR(20) DEFAULT '1.0.0',
    `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `end_time` TIMESTAMP NULL,
    `duration_seconds` INT DEFAULT 0,
    CONSTRAINT `fk_app_sessions_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 6. Tabla de Eventos de la App (Telemetría)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `app_events` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` INT NULL,
    `user_id` INT NULL,
    `event_name` VARCHAR(100) NOT NULL,
    `screen_name` VARCHAR(50) DEFAULT 'home',
    `duration_seconds` INT DEFAULT 0,
    `metadata_json` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_app_events_session`
        FOREIGN KEY (`session_id`) REFERENCES `app_sessions` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_app_events_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

