# How to Enable Email Verification for Admin Setup

The LMS now supports sending verification codes via email. To enable this feature, you must configure your email credentials.

## 1. Get an App Password (for Gmail)
1. Go to your **Google Account Settings**.
2. Navigate to **Security** > **2-Step Verification**.
3. Scroll down to **App passwords**.
4. Create a new App Password (e.g., name it "LMS App").
5. Copy the generated 16-character password.

## 2. Updated your .env file
Open the validation `.env` file in the project root (`c:\Users\kevin\Music\LMS_NTC\LMS_trial\LMS_trial\.env`) and add the following lines:

```env
EMAIL_SENDER="your-email@gmail.com"
EMAIL_PASSWORD="your-app-password-here"
```

## 3. Restart the Backend
Stop the current backend process (Ctrl+C) and restart it:
```bash
uvicorn api.app:app --reload
```

## Troubleshooting
If the email is not sent, the system will **automatically fallback** and print the OTP to the server console as before. Check the console logs for warnings or errors.
