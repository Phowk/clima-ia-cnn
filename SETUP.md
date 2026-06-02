# Instrucciones de Setup

## Setup de Backend

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd proyecto_web
```

### 2. Crear un virtual environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Correr el servidor backend
```bash
cd backend
uvicorn app.main:app --reload
```

La api estará disponible en `http://localhost:8000`

**Documentación de API:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Setup de Frontend

Abrir `frontend/index.html` o `frontend/deforestacion.html` en el navegador, o usando la extensión Live Server

Luego navegar al puerto correspondiente.

## Problemas frecuentes

- **ModuleNotFoundError**: Asegúrate de que el virtual environment esté corriendo
- **Port already in use (8000)**: Usar `uvicorn app.main:app --reload --port 8001`
- **TensorFlow issues**: Asegúrate de que estás usando Python 3.8 - 3.11
