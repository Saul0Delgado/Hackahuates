#!/bin/bash

echo "========================================"
echo " SmartCart AI - Inicio Automático"
echo "========================================"
echo ""

echo "[1/3] Iniciando Backend (Python API)..."
cd ConsumptionPrediction
source venv/bin/activate
python run_api.py &
BACKEND_PID=$!
cd ..

echo ""
echo "[2/3] Esperando 5 segundos para que el backend inicie..."
sleep 5

echo ""
echo "[3/3] Iniciando Frontend (React)..."
cd Frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo " LISTO!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Para detener ambos servidores:"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Abriendo navegador en 3 segundos..."
sleep 3

# Try different browser commands
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5173
elif command -v open > /dev/null; then
    open http://localhost:5173
else
    echo "No se pudo abrir el navegador automáticamente."
    echo "Por favor abre: http://localhost:5173"
fi

echo ""
echo "Presiona Ctrl+C para salir"
wait
