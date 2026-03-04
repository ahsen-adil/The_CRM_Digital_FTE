@echo off
echo ================================================================================
echo COMPLETE CRM SYSTEM - CURL TEST SUITE
echo ================================================================================
echo.

REM Wait for services to start
echo Waiting 5 seconds for services to start...
timeout /t 5 >nul

echo.
echo ================================================================================
echo TEST 1: HEALTH CHECKS
echo ================================================================================
echo.

echo Testing Unified Health Endpoint...
curl -s http://localhost:8002/health | findstr /C:"status" /C:"service"
echo.

echo Testing Webform Health...
curl -s http://localhost:8001/health | findstr /C:"status"
echo.

echo Testing WhatsApp Health...
curl -s http://localhost:8000/health | findstr /C:"status" /C:"kafka"
echo.

echo Testing API Server Health...
curl -s http://localhost:8002/api/v1/health | findstr /C:"status" /C:"database"
echo.

echo.
echo ================================================================================
echo TEST 2: WEBFORM CHANNEL
echo ================================================================================
echo.

echo Submitting webform...
curl -X POST http://localhost:8001/api/v1/webform/submit ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Curl Test\",\"email\":\"curl@test.com\",\"subject\":\"Curl E2E Test\",\"message\":\"Testing webform with curl commands\",\"priority\":\"normal\"}"
echo.
echo.

echo Verifying ticket created...
curl -s "http://localhost:8002/api/v1/tickets?channel=web_form&limit=1" | findstr /C:"ticket_number" /C:"channel"
echo.

echo.
echo ================================================================================
echo TEST 3: API SERVER ENDPOINTS
echo ================================================================================
echo.

echo Getting tickets list...
curl -s "http://localhost:8002/api/v1/tickets?limit=3" | findstr /C:"total" /C:"page"
echo.

echo Getting customers list...
curl -s "http://localhost:8002/api/v1/customers?limit=3" | findstr /C:"total" /C:"page"
echo.

echo Getting reports overview...
curl -s "http://localhost:8002/api/v1/reports/overview" | findstr /C:"total_tickets" /C:"total_customers"
echo.

echo.
echo ================================================================================
echo TEST 4: WHATSAPP WEBHOOK
echo ================================================================================
echo.

echo Simulating WhatsApp webhook...
curl -X POST http://localhost:8000/whatsapp-webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"messages\":[{\"id\":\"test-123\",\"from_me\":false,\"type\":\"text\",\"chat_id\":\"923001234567@s.whatsapp.net\",\"timestamp\":1234567890,\"text\":{\"body\":\"Test message from curl\"},\"from\":\"923001234567\",\"from_name\":\"Curl Test\"}]}"
echo.
echo.

echo.
echo ================================================================================
echo TEST 5: ROOT ENDPOINTS
echo ================================================================================
echo.

echo Testing root endpoint...
curl -s http://localhost:8002/ | findstr /C:"service" /C:"channels"
echo.

echo.
echo ================================================================================
echo TEST SUMMARY
echo ================================================================================
echo.
echo Check output above for results:
echo   [OK] = Service responded correctly
echo   [FAIL] = Service did not respond or error occurred
echo.
echo ================================================================================

pause
