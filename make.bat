@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

set "VENV_SCRIPTS=C:\sandbox\venv_spicelib\Scripts"
set "SPHINXBUILD=%VENV_SCRIPTS%\sphinx-build.exe"
set "SOURCEDIR=doc"
set "BUILDDIR=doc_build"
set "SPICELIB_SRC=C:\sandbox\spicelib_dev\"
if defined PYTHONPATH (
	set "PYTHONPATH=%SPICELIB_SRC%;%PYTHONPATH%"
) else (
	set "PYTHONPATH=%SPICELIB_SRC%"
)
set "PATH=%VENV_SCRIPTS%;%PATH%"

if not exist "%SPHINXBUILD%" (
	echo.
	echo.The virtualenv Sphinx executable was not found:
	echo.%SPHINXBUILD%
	echo.
	exit /b 1
)

if "%1" == "" goto help

"%SPHINXBUILD%" >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found in the virtualenv:
	echo.%VENV_SCRIPTS%
	echo.
	exit /b 1
)

"%SPHINXBUILD%" -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
"%SPHINXBUILD%" -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
