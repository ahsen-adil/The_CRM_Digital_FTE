@echo off
echo ============================================================
echo WHATSAPP WEBHOOK TEST
echo ============================================================
echo.
echo Sending test message to WhatsApp webhook server...
echo.

curl -X POST http://localhost:8000/test-webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"923001234567\", \"from_name\": \"Test User\", \"message\": \"Hello, I need help with my order\"}"

echo.
echo ============================================================
echo Check the server window for processing logs!
echo ============================================================
pause
