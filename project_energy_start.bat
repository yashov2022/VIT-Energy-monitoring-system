@echo off

REM 🔹 Set environment Python path
set PYTHON_PATH=C:\Users\Admin\.spyder-py3\energy310\Scripts\python.exe
set STREAMLIT_PATH=C:\Users\Admin\.spyder-py3\energy310\Scripts\streamlit.exe

REM 🔹 MAIN DASHBOARD
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\main00ML.py --server.headless true --server.address 0.0.0.0 --server.port 8501

REM 🔹 BUILDING DASHBOARDS
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\SJT_1.py --server.headless true --server.address 0.0.0.0 --server.port 8502
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\SJT_2.py --server.headless true --server.address 0.0.0.0 --server.port 8503
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\SJT_3.py --server.headless true --server.address 0.0.0.0 --server.port 8504
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\TT_1.py --server.headless true --server.address 0.0.0.0 --server.port 8505
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\TT_2.py --server.headless true --server.address 0.0.0.0 --server.port 8506
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\MB_1.py --server.headless true --server.address 0.0.0.0 --server.port 8507
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\MB_2.py --server.headless true --server.address 0.0.0.0 --server.port 8508

REM 🔹 HPHI
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHI_1.py --server.headless true --server.address 0.0.0.0 --server.port 8509
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHI_2.py --server.headless true --server.address 0.0.0.0 --server.port 8510
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHI_3.py --server.headless true --server.address 0.0.0.0 --server.port 8511
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHI_4.py --server.headless true --server.address 0.0.0.0 --server.port 8512

REM 🔹 HPHII
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHII_1.py --server.headless true --server.address 0.0.0.0 --server.port 8513
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHII_2.py --server.headless true --server.address 0.0.0.0 --server.port 8514

REM 🔹 HPHIII
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHIII_1.py --server.headless true --server.address 0.0.0.0 --server.port 8515
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHIII_2.py --server.headless true --server.address 0.0.0.0 --server.port 8516

REM 🔹 11kV PANELS
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\SJT_11kV.py --server.headless true --server.address 0.0.0.0 --server.port 8517
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\TT_11kV.py --server.headless true --server.address 0.0.0.0 --server.port 8518
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\HPHII_11kV.py --server.headless true --server.address 0.0.0.0 --server.port 8519
start "" /B "%STREAMLIT_PATH%" run C:\Users\Admin\.spyder-py3\PRP_11kV.py --server.headless true --server.address 0.0.0.0 --server.port 8520
