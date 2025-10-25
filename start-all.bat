@echo off
echo ========================================
echo  SmartCart AI - Inicio Automatico
echo ========================================
echo.

echo [1/3] Iniciando Backend (Python API)...
start "SmartCart Backend" cmd /k "cd ConsumptionPrediction && venv\Scripts\activate && python run_api.py"

echo.
echo [2/3] Esperando 5 segundos para que el backend inicie...
timeout /t 5 /nobreak > nul

echo.
echo [3/3] Iniciando Frontend (React)...
start "SmartCart Frontend" cmd /k "cd Frontend && npm run dev"

echo.
echo ========================================
echo  LISTO! Abriendo navegador...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.

timeout /t 3 /nobreak > nul
start http://localhost:5173

echo.
echo Presiona cualquier tecla para cerrar esta ventana.
echo Las otras ventanas seguiran corriendo.
pause > nul
