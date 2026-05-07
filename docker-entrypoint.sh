#!/bin/sh
set -e

echo "🚀 Iniciando Kimi Workspace..."

# Esperar a que PostgreSQL esté disponible
echo "⏳ Esperando PostgreSQL..."
until nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL listo"

# Ejecutar migraciones de Prisma
echo "🔄 Ejecutando migraciones..."
npx prisma migrate deploy

# Iniciar la aplicación
echo "🌐 Iniciando Next.js..."
exec npm start
