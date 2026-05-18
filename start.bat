@echo off
chcp 65001

:: 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

echo ========================================
echo 智能体评估系统 - 启动脚本
echo ========================================
echo 当前目录: %CD%
echo.

:: 检查后端虚拟环境
echo [1/3] 检查后端环境
echo 检查路径: "%CD%\BackEnd\.venv"
if not exist "BackEnd\.venv" (
    echo [错误] 后端虚拟环境不存在
    echo.
    echo 当前检查的路径: "%CD%\BackEnd\.venv"
    echo.
    echo 请先创建虚拟环境：
    echo   cd BackEnd
    echo   python -m veimage.pngnv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "BackEnd\.venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境激活脚本不存在
    echo 请重新创建虚拟环境
    pause
    exit /b 1
)

echo [OK] 后端虚拟环境检查通过

:: 检查 MySQL 服务（如果使用 MySQL）
echo 检查数据库配置
cd BackEnd
if exist ".env" (
    findstr /C:"DB_DRIVER=mysql" .env >nul 2>&1
    if not errorlevel 1 (
        echo 检测到 MySQL 配置，正在检查 MySQL 服务...
        :: 尝试连接 MySQL 测试服务是否运行
        call .venv\Scripts\python.exe -c "import pymysql; import os; from dotenv import load_dotenv; load_dotenv(); pymysql.connect(host=os.getenv('DB_HOST', '127.0.0.1'), port=int(os.getenv('DB_PORT', '3306')), user=os.getenv('DB_USER', 'root'), password=os.getenv('DB_PASSWORD', ''), connect_timeout=2).close()" >nul 2>&1
        if errorlevel 1 (
            echo [警告] MySQL 服务未运行或无法连接
            echo.
            echo 请先启动 MySQL 服务：
            echo   方法1: 运行 BackEnd\start_mysql.bat（推荐）
            echo   方法2: 在服务管理器中启动 MySQL 服务
            echo   方法3: 以管理员身份运行: net start MySQL
            echo   方法4: 使用 MySQL Workbench 启动
            echo.
            echo 或者按任意键继续（如果 MySQL 服务已在后台运行）
            pause >nul
        ) else (
            echo [OK] MySQL 服务连接正常
        )
    )
)
cd ..

:: 检查uvicorn是否安装
echo 检查依赖安装情况
cd BackEnd
call .venv\Scripts\python.exe -m pip show uvicorn >nul 2>&1
if errorlevel 1 (
    echo [警告] uvicorn 未安装，正在安装依赖
    call .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        cd ..
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] 依赖检查通过
)
cd ..
echo.

:: 检查前端node_modules
echo [2/3] 检查前端环境
if not exist "FrontEnd\node_modules" (
    echo [警告] 前端依赖未安装
    echo 正在安装前端依赖
    cd FrontEnd
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
    cd ..
    echo [OK] 前端依赖安装完成
) else (
    echo [OK] 前端依赖检查通过
)
echo.

:: 启动后端服务
echo [3/3] 启动服务
echo.
echo 正在启动后端服务（端口 8000）
start "Backend Service" cmd /k "cd /d %~dp0BackEnd && .venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: 等待后端启动
echo 等待后端服务启动...
timeout /t 3 /nobreak

echo 正在启动前端服务（端口 5173）
start "Frontend Service" cmd /k "cd /d %~dp0FrontEnd && npm run dev"

:: 等待前端启动
timeout /t 2 /nobreak

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 后端地址: http://127.0.0.1:8000
echo 前端地址: http://127.0.0.1:5173
echo API文档:  http://127.0.0.1:8000/docs
echo.
echo 提示: 两个服务窗口已打开，关闭窗口即可停止服务
echo.
echo 注意: 如果服务未正常启动，请检查新打开的窗口中的错误信息
echo.
pause