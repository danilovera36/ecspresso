# ☕ ecspresso

**ecspresso** es una herramienta de DevOps diseñada para centralizar y automatizar la gestión de variables de entorno, secretos (AWS SSM) y plantillas de *Task Definitions* para despliegues en Amazon ECS (Elastic Container Service). 

Permite a los equipos de desarrollo y DevOps gestionar las configuraciones de múltiples aplicaciones y entornos (`development`, `staging`, `production`) a través de una API robusta y una herramienta de línea de comandos (CLI) interactiva y visual.

---

## 🚀 Características Principales

- **Gestión Centralizada:** Define las plantillas base JSON de tus contenedores de ECS.
- **Merge de Variables y Secretos:** Inyecta automáticamente variables de entorno y referencias de secretos (AWS Systems Manager Parameter Store).
- **Herramienta CLI Enriquecida:** Construida con `click` y `rich` para mostrar salidas formateadas (con sintaxis y color) directamente en la terminal.
- **Autenticación Dual:**
  - UI Web protegida por **JWT** y Password Hashing (`bcrypt`).
  - API protegida por **API Key** (para su uso de forma automatizada en pipelines CI/CD y por la CLI).
- **Producción Lista:**
  - Aplicación contenerizada (`Dockerfile` unprivileged running).
  - Endpoint dedicado de Health Check (`/health`).
  - Desplegable localmente con `docker-compose`.
  - Capa de abstracción limpia de base de datos (Patrón Repository / CRUD).

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** FastAPI, Uvicorn
- **Base de Datos:** PostgreSQL, SQLAlchemy (ORM)
- **Seguridad:** PyJWT, Bcrypt
- **CLI:** Click, Rich, Requests
- **Infraestructura Base:** Docker, Docker Compose

---

## 🏃‍♂️ Instalación y Puesta en Marcha

### 1. Configuración de Variables de Entorno y AWS (SSM)
El proyecto utiliza un archivo `.env` para gestionar secretos, credenciales de Base de Datos y de AWS securely (para evitar subirlos a repositorios).

Copia el archivo de ejemplo para crear tu entorno local:
```bash
cp .env.example .env
```
Luego edita `.env` agregando tus credenciales de AWS y cambiando las contraseñas si fuera necesario.

### 2. Levantar la Infraestructura

Clona el repositorio y levanta la base de datos PostgreSQL junto con la API usando Docker Compose. Esto además construirá la nueva imagen con el usuario sin privilegios.

```bash
sudo docker compose up -d --build
```

Esto expondrá la API de FastAPI en `http://localhost:8000`.

### 3. Poblar la Base de Datos (Seed)
Para autenticarte de forma local u observar datos precargados, usa el servicio de semilla de datos principal.

```bash
sudo docker exec -it ecspresso-api-1 python seed.py
```
*(Crea al usuario `admin` con contraseña `admin`)*

**Datos de Prueba (Opcional):**
Si quieres cargar datos falsos (mock) sobre una Task Definition local para jugar con la CLI sin AWS real, añade el flag `--mock`:

```bash
sudo docker exec -it ecspresso-api-1 python seed.py --mock
```

---

## 💻 Uso en CI/CD y CLI (Autenticación por API Key)

Tanto tu línea de comandos local como los pipelines de CI/CD (por ejemplo, **GitHub Actions** o **Jenkins**) interactúan con `ecspresso` mediante autenticación por **API Key**. Esto evita tener que gestionar sesiones o expiraciones de Tokens JWT en entornos automatizados.

### 1. ¿Cómo crear una nueva API Key para tu Pipeline?

La API Key viaja en texto plano desde el cliente (tu CLI o Jenkins), pero en el servidor (`docker-compose.yml`) se guarda de forma segura como un hash de `bcrypt`.

Si deseas crear tu propia clave secreta (ej. `mi-clave-super-segura`), primero debes generar su Hash usando Python en tu terminal:

```bash
python -c 'import bcrypt; print(bcrypt.hashpw(b"mi-clave-super-segura", bcrypt.gensalt()).decode().replace("$", "$$"))'
```

Copia la salida (el hash que empieza con `$$2b$$...`) y pégalo en la variable `API_KEY_HASH` dentro de tu archivo `docker-compose.yml`. Luego reinicia el contenedor para que la tome.

### 2. Configuración en GitHub Actions / Jenkins / CLI

Una vez el backend conoce el hash, debes configurar tu pipeline (o tu entorno local) inyectando la llave original en texto plano mediante variables de entorno:

```bash
export ECSPRESSO_API_KEY="mi-clave-super-segura"
export ECSPRESSO_URL="http://localhost:8000" # Opcional, por defecto apunta ahí
```
*(En GitHub Actions guardarías `mi-clave-super-segura` como un GitHub Secret y se lo inyectarías al job).*

---

## 🔧 Uso de la CLI

#### 1. Obtener una Task Definition
Devuelve el JSON final de la *Task Definition* listo para inyectarse en el comando de AWS CLI (con sintaxis enriquecida):

```bash
python cli.py td get --app payment-service --env development
```
*Si deseas guardarlo en un archivo, añade el flag `--output td.json` o `-o td.json`.*

#### 2. Establecer una Variable de Entorno
Crea la aplicación (si no existe) y define la variable al vuelo para un entorno específico:

```bash
python cli.py set-var --app my-app --env development --key DB_HOST --value localhost
```

#### 3. Establecer un Secreto (AWS SSM)
Define un secreto de forma remota y guarda la referencia segura:

```bash
python cli.py set-secret --app my-app --env development --key STRIPE_API_KEY --value sk_test_1234
```

---

## 🔗Endpoints Principales de la API

| Método | Endpoint | Descripción | Requiere Autenticación |
|---|---|---|---|
| `GET` | `/` | Retorna el dashboard estático en HTML | - |
| `GET` | `/health` | Health Check (verifica conexión a Base de Datos) | - |
| `POST`| `/api/v1/auth/login` | Otorga el token JWT para el frontend | Basic HTTP |
| `GET` | `/api/v1/apps/{app_name}/td` | Genera y combina el JSON de ECS | *JWT* o *API Key* |

---

## 🔐 Seguridad y Notas de Diseño

- El `Dockerfile` se construyó bajo estándares seguros de producción, removiendo root flags y creando un `appuser` aislado.
- Todos los passwords y tokens son asegurados mediante algoritmos actualizados de hashing en un solo sentido. El token provisto estáticamente en tu docker-compose local (`my-secret-api-key`) no debe ser reutilizado en verdaderos ambientes productivos.

---
*Construido para automatizar la vida de los DevOps.*
