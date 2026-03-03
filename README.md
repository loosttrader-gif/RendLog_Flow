# RendLog Flow

Plataforma de analisis estadistico en tiempo real para trading. Detecta anomalias en rendimientos logaritmicos (RendLog) y flujo de ordenes (OrderFlow) usando datos de MetaTrader 5.

---

## Requisitos

Antes de comenzar, asegurate de contar con lo siguiente:

1. **Python 3.10.2 o superior** instalado en tu PC ([Descargar Python](https://www.python.org/downloads/))
2. **MetaTrader 5** instalado con una cuenta activada (demo o real)
3. **Cuenta registrada en RendLog Flow** — registrate en la plataforma web para obtener tu API Key

---

## Instalacion del Backend

### 1. Descargar el backend

Abre una terminal y ejecuta:

```bash
git clone https://github.com/loosttrader-gif/RendLog_Flow.git
```

Esto descarga todo el proyecto. El backend esta en la carpeta `backend/`.

### 2. Instalar dependencias

Navega a la carpeta del backend e instala las librerias necesarias:

```bash
cd RendLog_Flow/backend
pip install -r requirements.txt
```

### 3. Configurar el archivo .env

Dentro de la carpeta `backend/` encontraras un archivo `.env`. Abrelo con cualquier editor de texto y completa las siguientes variables:

```env
# MT5 Credentials (TU CUENTA)
MT5_LOGIN=12345678
MT5_PASSWORD=tu_password_aqui
MT5_SERVER=NombreDeTuBroker-Demo

# API Key del usuario (la obtienes al registrarte en la plataforma web)
API_KEY=rnd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Variables que debes modificar:**

| Variable | Que poner | Ejemplo |
|---|---|---|
| `MT5_LOGIN` | Numero de tu cuenta MT5 | `12345678` |
| `MT5_PASSWORD` | Password de tu cuenta MT5 | `miPassword123` |
| `MT5_SERVER` | Servidor de tu broker | `Tickmill-Demo` |
| `API_KEY` | Tu API Key de RendLog Flow | `rnd_b15ec1855bbdef...` |

> **Importante:** Las variables `SUPABASE_URL` y `SUPABASE_ANON_KEY` ya vienen configuradas. No las modifiques.

---

## Uso diario

### Paso 1: Abrir MetaTrader 5

Abre MT5 e inicia sesion con tu cuenta (demo o real). Asegurate de que el par **EURUSD** este visible en tu Market Watch.

### Paso 2: Iniciar sesion en la plataforma web

Ingresa a la plataforma RendLog Flow desde tu navegador e inicia sesion con tu cuenta registrada. Aqui veras el dashboard con tus datos en tiempo real.

### Paso 3: Ejecutar el backend

1. Abre el **Explorador de Archivos** y navega hasta la carpeta donde descargaste el proyecto, por ejemplo: `Documentos > RendLog_Flow > backend`
2. Haz **clic derecho** en un espacio vacio de la carpeta y selecciona **"Abrir en Terminal"**
3. En la terminal, ejecuta:

```bash
python main.py
```

Veras algo como esto:

```
======================================================================
          RENDLOG PLATFORM V4.0 - Ventana Movil 60 Velas
======================================================================
[2026-03-02 10:00:00] Conectado a MT5 - Tickmill-Demo
[2026-03-02 10:00:01] Usuario autenticado: xxxxxxxx-xxxx-xxxx
[2026-03-02 10:00:01] Limpiando datos anteriores del usuario...
[2026-03-02 10:00:02] Carga inicial: 60 velas por timeframe...
[2026-03-02 10:00:05] Carga inicial completada: 354 filas
[2026-03-02 10:00:05] Iniciando loop de ventana movil (cada 30s)...
```

El backend queda corriendo y actualizando datos cada 30 segundos. Para detenerlo, presiona `Ctrl+C`.

### Paso 4: Ver datos en el dashboard

Regresa a la plataforma web. Tu dashboard se actualizara automaticamente con los datos que el backend esta enviando.

---

## Resumen rapido

```
1. Abrir MT5 (con sesion iniciada)
2. Iniciar sesion en la plataforma web
3. Abrir terminal en la carpeta backend/
4. Ejecutar: python main.py
5. Ver el dashboard en tiempo real
```

---

## Solucion de problemas

| Problema | Solucion |
|---|---|
| "No se pudo conectar a MT5" | Verifica que MT5 este abierto y con sesion activa |
| "API_KEY no configurada o invalida" | Revisa tu API_KEY en el archivo `.env` |
| "No se pudieron obtener datos" | Asegurate de que EURUSD este visible en Market Watch de MT5 |
| El dashboard no muestra datos | Verifica que el backend este corriendo (`python main.py`) |
