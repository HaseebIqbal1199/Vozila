@echo off
REM Quick deployment preparation script for Windows

echo 🚀 Preparing YouTube Downloader for Railway deployment...
echo.

REM Check if git is initialized
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo.
)

REM Add all files to git
echo Adding files to git...
git add .
echo.

REM Check if there are changes to commit
git diff --staged --quiet
if errorlevel 1 (
    echo Committing changes...
    git commit -m "Prepare for Railway deployment - %date% %time%"
    echo.
) else (
    echo No changes to commit.
    echo.
)

REM Check if origin remote exists
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  Please add your GitHub repository as origin:
    echo    git remote add origin https://github.com/yourusername/your-repo.git
    echo    git push -u origin main
    echo.
) else (
    echo Pushing to GitHub...
    git push
    echo.
)

echo ✅ Deployment preparation complete!
echo.
echo 📋 Next steps:
echo 1. Go to railway.app and create a new project
echo 2. Connect your GitHub repository
echo 3. Deploy your application
echo 4. Configure your custom domain
echo 5. Run: python seo_analyzer.py your-domain.com
echo.

pause
