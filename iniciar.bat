@echo off
chcp 65001 > nul
title DespensAPP - Lanzador Rápido

echo ========================================================
echo       Bienvenido a DespensAPP (Suite Universitaria)
echo ========================================================
echo.

:: 1. Verificar si Python está instalado en el sistema
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no fue detectado en el PATH de este equipo.
    echo Por favor instala Python 3.10 o superior marcando "Add Python to PATH".
    pause
    exit /b 1
)

:: 2. Crear el entorno virtual si no existe
if not exist "venv\Scripts\python.exe" (
    echo [PASO 1/2] Creando entorno virtual local (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [PASO 2/2] Instalando dependencias desde requirements.txt...
    .\venv\Scripts\python.exe -m pip install --upgrade pip
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ADVERTENCIA] Algunas dependencias tuvieron problemas al instalarse.
    )
    echo.
    echo [OK] Entorno configurado exitosamente.
    echo.
)

:: 3. Menú interactivo de ejecución
:MENU
cls
echo ========================================================
echo             DESPENSAPP - PANEL DE CONTROL
echo ========================================================
echo  [1] Iniciar App Móvil (Kivy / KivyMD)
echo  [2] Iniciar Dashboard Web de Analítica (FastAPI)
echo  [3] Iniciar Ambos (Dashboard Web + App Móvil)
echo  [4] Reinstalar / Actualizar dependencias
echo  [5] Salir
echo ========================================================
set /p OPCION="Selecciona una opción (1-5): "

if "%OPCION%"=="1" goto APP
if "%OPCION%"=="2" goto DASHBOARD
if "%OPCION%"=="3" goto AMBOS
if "%OPCION%"=="4" goto REINSTALL
if "%OPCION%"=="5" goto SALIR

echo Opción no válida. Intenta de nuevo.
timeout /t 2 >nul
goto MENU

:APP
cls
echo [INFO] Iniciando DespensAPP Móvil...
echo (Si XAMPP no está encendido, se usará la base de datos local SQLite automáticamente).
echo.
.\venv\Scripts\python.exe main.py
pause
goto MENU

:DASHBOARD
cls
echo [INFO] Iniciando Servidor de Analítica y Dashboard Web...
echo Abre tu navegador en: http://localhost:8000/dashboard
echo Documentación API en: http://localhost:8000/docs
echo Presiona Ctrl+C en esta ventana para detener el servidor.
echo.
start http://localhost:8000/dashboard
.\venv\Scripts\python.exe admin_dashboard/server.py
pause
goto MENU

:AMBOS
cls
echo [INFO] Levantando Dashboard Web en segundo plano...
start "DespensAPP Web Dashboard" cmd /k ".\venv\Scripts\python.exe admin_dashboard/server.py"
timeout /t 2 >nul
start http://localhost:8000/dashboard
echo [INFO] Iniciando App Móvil...
.\venv\Scripts\python.exe main.py
goto MENU

:REINSTALL
cls
echo [INFO] Actualizando dependencias...
.\venv\Scripts\python.exe -m pip install -r requirements.txt
pause
goto MENU

:SALIR
exit /b 0
