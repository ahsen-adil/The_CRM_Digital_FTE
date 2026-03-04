@echo off
echo ============================================================
echo STABLE EMAIL POLLING SYSTEM - TEST SCRIPT
echo ============================================================
echo.
echo This script will:
echo 1. Start the email polling service
echo 2. Wait for you to send a test email
echo 3. Show you the results
echo.
echo BEFORE RUNNING:
echo - Make sure you have access to a SECOND Gmail account
echo - Know your Gmail App Password for the second account
echo.
pause

echo.
echo [STEP 1] Starting email polling service...
echo.
start "Email Polling Service" cmd /k "cd /d %~dp0 && python poll_emails.py"

echo Waiting 5 seconds for service to start...
timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo [STEP 2] SEND A TEST EMAIL NOW
echo ============================================================
echo.
echo From: YOUR SECOND GMAIL ACCOUNT (e.g., ahsenadil2@gmail.com)
echo To: meoahsan01@gmail.com
echo Subject: TEST EMAIL
echo Body: Hi, this is a test email.
echo.
echo IMPORTANT:
echo - Do NOT open Gmail on meoahsan01@gmail.com
echo - Keep the polling service window open
echo - Watch for the email to be detected and processed
echo.
echo After sending the email, wait up to 60 seconds.
echo.
pause

echo.
echo [STEP 3] Checking results...
echo.
echo The polling service window should show:
echo - [EMAIL RECEIVED]
echo - [STEP 1/7] Creating/finding customer
echo - [STEP 2/7] Creating conversation
echo - [STEP 3/7] Creating ticket
echo - [STEP 4/7] Calling AI agent
echo - [STEP 5/7] Logging AI interaction
echo - [STEP 6/7] No escalation required (or escalation created)
echo - [STEP 7/7] Sending AI-generated reply via SMTP
echo - [SMTP] REPLY SENT SUCCESSFULLY
echo.
echo Check your SECOND Gmail account for the AI reply!
echo.
pause

echo.
echo To stop the polling service, close its window or press Ctrl+C
echo.
echo ============================================================
echo TEST COMPLETE
echo ============================================================
