# VideoManager
repository for video manager app
"""README.md: VideoManager - Application Installation & Usage Guide"""

# VideoManager - Video Organizer Application

Una aplicación completa de escritorio para organizar, gestionar y visualizar archivos de video con interfaz gráfica Tkinter.

## ✅ Características Implementadas

### 1. **Importación de Videos**
- ✅ Importar videos individuales (`Agregar Video`)
- ✅ Importar carpetas completas de manera recursiva (`Agregar Carpeta`)
- ✅ Soporta múltiples formatos: mp4, mkv, avi, mov, flv, wmv, webm
- ✅ Almacenamiento en base de datos SQLite

### 2. **Vistas de Video**
- ✅ **Grid View**: Galería de miniaturas con layout responsivo (1-4 columnas)
- ✅ **List View**: Tabla detallada con ordenamiento por columnas
- ✅ **Timeline View**: Línea temporal con miniaturas de frames (preparado para FFmpeg)

### 3. **Metadatos de Video**
- ✅ **Categorías**: public, private, ticket, password, special, clip, other
- ✅ **Rating**: Sistema de 1-5 estrellas interactivo
- ✅ **Notas**: Campo de comentarios sin límite de caracteres
- ✅ **Información**: Título, ruta, duración, fecha de adición

### 4. **Reproductor**
- ✅ Integración con VLC (si está instalado)
- ✅ Controles: Play, Pause, Stop
- ✅ Sincronización con timeline (preparado)

### 5. **Base de Datos**
- ✅ Almacenamiento persistente en SQLite
- ✅ Esquema completo con todos los campos necesarios
- ✅ Validación de duplicados por ruta

---

## 📋 Requisitos del Sistema

### Python
- **Python 3.7+** recomendado (3.8+)
- Windows, macOS o Linux

### Librerías Python (obligatorias)
```bash
pip install Pillow
```

### Librerías Python (opcionales)
```bash
pip install python-vlc  # Para reproductor VLC
pip install ffmpeg-python  # Para generación de timelines (futuro)
```

### Software Externo (opcional)
- **VLC Media Player**: Necesario para reproducción de video
  - Windows: Descargar de https://www.videolan.org/vlc/
  - macOS: `brew install vlc`
  - Linux: `sudo apt-get install vlc`

---

## 🚀 Instalación y Ejecución

### Opción 1: Lanzador Directo (Recomendado)

```bash
python launch_videomanager.py
```

### Opción 2: Ejecutar módulo directamente

```bash
python videomanager.py
```

### Opción 3: Crear acceso directo en Windows

1. Crea un archivo `.bat` con el contenido:
```batch
@echo off
python launch_videomanager.py
pause
```

2. Guarda como `VideoManager.bat` en la carpeta
3. Haz doble clic para ejecutar

---

## 📖 Guía de Uso

### Importar Videos

#### Método 1: Video Individual
1. Clic en botón **➕ Add Video**
2. Selecciona un archivo de video
3. Se agregará a la BD y aparecerá en las vistas

#### Método 2: Carpeta Completa
1. Clic en botón **📁 Add Folder**
2. Selecciona una carpeta
3. Se importarán todos los videos de esa carpeta y subcarpetas

### Visualizar Videos

#### Grid View (Pestaña "Grid View")
- Muestra miniaturas tipo galería
- Haz clic en cualquier miniatura para seleccionar
- Scroll con rueda de ratón

#### List View (Pestaña "List View")
- Muestra tabla con 6 columnas: Format, Title, Duration, Category, Rating, Notes
- Haz clic en una fila para seleccionar
- Puedes hacer clic en encabezados para ordenar

#### Timeline (Pestaña "Timeline")
- Muestra miniaturas de diferentes frames del video
- Haz clic en un frame para saltar a esa posición en el reproductor

### Editar Video

Cuando seleccionas un video en cualquier vista:

1. **Panel derecho** muestra los detalles editable:
   - **Title**: Título del video (solo lectura aquí)
   - **Path**: Ruta del archivo (solo lectura)
   - **Category**: Selecciona categoría con dropdown
   - **Rating**: Haz clic en estrellas para calificar (1-5)
   - **Notes**: Escribe comentarios

2. **Guardar cambios**:
   - Clic en botón **Save** para guardar
   - Clic en botón **Cancel** para descartar cambios

### Reproducir Video

Panel inferior "Player":
- Se carga automáticamente cuando seleccionas un video
- Botones: ▶ Play, ⏸ Pause, ⏹ Stop
- Si VLC está instalado, puedes ver la reproducción

### Eliminar Video

1. Selecciona un video en cualquier vista
2. Clic en botón **🗑️ Delete**
3. Confirma la eliminación
4. El video se borra de la BD

### Refrescar Vista

- Clic en botón **🔄 Refresh** para recargar todos los videos

---

## 🗄️ Estructura de Archivos

```
video_organizer/
├── videomanager.py           # Aplicación principal
├── launch_videomanager.py    # Script de lanzamiento
├── video_db.py               # Módulo de base de datos SQLite
├── ui_preview.py             # Módulo de vistas (Grid, List, Timeline)
├── ui_edit.py                # Módulo de editor de metadatos
├── ui_player.py              # Módulo de reproductor VLC
├── videos.db                 # Base de datos SQLite (creada automáticamente)
├── EXECUTIVE_SUMMARY.md      # Resumen ejecutivo de requisitos
├── ARCHITECTURE_DETAILED.md  # Documentación de arquitectura
├── FUNCTIONS_DETAILED.md     # Documentación de funciones
└── README.md                 # Este archivo
```

---

## 🗄️ Esquema de Base de Datos

```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    path TEXT UNIQUE NOT NULL,
    title TEXT,
    duration TEXT,
    category TEXT DEFAULT 'public',
    rating INTEGER DEFAULT 0,
    notes TEXT,
    thumbnail BLOB,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Campos:
- **id**: Identificador único del video
- **filename**: Nombre del archivo
- **path**: Ruta completa del archivo
- **title**: Título mostrado en la app
- **duration**: Duración del video (MM:SS)
- **category**: Categoría (public, private, ticket, password, clip, special, other)
- **rating**: Calificación 0-5 estrellas
- **notes**: Comentarios/notas del usuario
- **thumbnail**: Miniatura (BLOB, futuro)
- **added_date**: Fecha de importación

---

## 🐛 Solución de Problemas

### Error: "No module named 'tkinter'"
```bash
# Windows: tkinter viene con Python, reinstala Python asegurando esta opción
# Linux: instala tkinter
sudo apt-get install python3-tk

# macOS: tkinter viene con Python
```

### Error: "No module named 'PIL'"
```bash
pip install Pillow
```

### Reproductor no funciona
```bash
# Instala python-vlc
pip install python-vlc

# Instala VLC Media Player en el sistema
# Windows: https://www.videolan.org/vlc/
# macOS: brew install vlc
# Linux: sudo apt-get install vlc
```

### Base de datos corrupta
```bash
# Elimina el archivo videos.db para crear uno nuevo
rm videos.db
# O en Windows:
del videos.db

# Reinicia la aplicación
python launch_videomanager.py
```

---

## 📝 Notas de Desarrollo

### Características Futuras
- Generación automática de timelines con FFmpeg
- Búsqueda y filtrado avanzado
- Exportación de lista a CSV
- Sincronización con cloud storage
- Editor de miniatura personalizada
- Sistema de etiquetas/tags

### Extensibilidad
Los módulos están diseñados para ser fácilmente extensibles:
- `video_db.py`: Agregar nuevos campos a la BD
- `ui_preview.py`: Agregar nuevas vistas o mejorar Grid/List
- `ui_edit.py`: Agregar más campos editables
- `ui_player.py`: Integrar otros reproductores

---

## 📄 Licencia

Este proyecto es de código abierto. Siéntete libre de modificarlo y distribuirlo.

---

## 👨‍💻 Autor

Desarrollado como aplicación completa de organización de videos.

**Versión:** 1.0  
**Fecha:** Octubre 2025
