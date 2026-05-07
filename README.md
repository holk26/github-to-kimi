# GitHub → Kimi CLI

Aplicación web para listar todos tus repositorios de GitHub y abrirlos directamente en Kimi CLI.

## Características

- Lista todos tus repositorios de GitHub con paginación automática
- Búsqueda en tiempo real por nombre y descripción
- Filtros por lenguaje de programación
- Botón "Abrir en Kimi" que copia el comando necesario al portapapeles
- Interfaz oscura optimizada para desarrolladores

## Despliegue en Dokploy

### 1. Crear aplicación en Dokploy

1. Ve a tu panel de Dokploy
2. Crea un nuevo proyecto y entorno
3. Selecciona "Application" y conecta tu repositorio de Git

### 2. Configurar variables de entorno

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `GITHUB_TOKEN` | Token de acceso personal de GitHub | Sí |
| `GITHUB_USERNAME` | Tu nombre de usuario de GitHub (opcional, se detecta automáticamente) | No |

#### Cómo crear un GitHub Token

1. Ve a [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Genera un nuevo token (classic)
3. Selecciona el scope `repo` para acceder a repositorios privados
4. Copia el token y guárdalo en las variables de entorno de Dokploy

### 3. Configurar build

En Dokploy, configura el build type como **Dockerfile**.

### 4. Desplegar

Haz click en "Deploy" y tu aplicación estará lista.

## Uso local

```bash
# Clonar el repositorio
git clone <tu-repo>
cd my-app

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tu GITHUB_TOKEN

# Ejecutar en desarrollo
npm run dev
```

## Cómo funciona "Abrir en Kimi"

El botón "Abrir en Kimi" copia al portapapeles un comando como:

```bash
cd ~/repos 2>/dev/null || mkdir -p ~/repos && cd ~/repos && git clone git@github.com:usuario/repo.git && cd repo && kimi
```

Simplemente pega este comando en tu terminal y presiona Enter para:
1. Crear el directorio `~/repos` si no existe
2. Clonar el repositorio
3. Entrar al directorio
4. Abrir Kimi CLI

## Tecnologías

- Next.js 15 (App Router)
- React 19 + TypeScript
- Tailwind CSS v4
- shadcn/ui
- GitHub API

## Licencia

MIT
