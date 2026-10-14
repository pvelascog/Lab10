-- Extensiones requeridas (research.md D2). También se crean en la migración inicial.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Base de datos de pruebas para la suite de integración.
CREATE DATABASE validador_pruebas;
\connect validador_pruebas
CREATE EXTENSION IF NOT EXISTS pg_trgm;
