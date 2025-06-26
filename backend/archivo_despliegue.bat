a
 
CREATE TABLE `usuarios_chat` (

  `id` int NOT NULL AUTO_INCREMENT,

  `cedula` varchar(20) NOT NULL,

  `nombre_completo` varchar(100) NOT NULL,

  `activo` tinyint(1) DEFAULT '1',

  PRIMARY KEY (`id`),

  UNIQUE KEY `cedula` (`cedula`)

) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
 
https://chatgpt.com/share/67fd4b50-ccc8-8007-b78d-bee4d85e00bb
 
@echo off

setlocal enabledelayedexpansion
 
:: Obtener fecha actual en formato YYYY-MM-DD HH:MM:SS

for /f "tokens=1-3 delims=/" %%a in ("%date%") do (

    set day=%%a

    set month=%%b

    set year=%%c

)
 
for /f "tokens=1-2 delims=:." %%a in ("%time%") do (

    set hour=%%a

    set minute=%%b

)
 
:: Asegurar dos dígitos

if 1%hour% LSS 110 set hour=0%hour%

if 1%minute% LSS 110 set minute=0%minute%
 
set fecha=%year%-%month%-%day% %hour%:%minute%:00
 
:: Verificar si hay cambios

git status --porcelain > temp_git_status.txt

findstr /r /c:".*" temp_git_status.txt >nul

if %errorlevel%==1 (

    echo No hay cambios para desplegar. No se generó artefacto.

    del temp_git_status.txt

    exit /b 0

)

del temp_git_status.txt
 
:: Leer versión actual

set /p version_actual=<version
 
:: Separar versión: major.minor.patch

for /f "tokens=1-3 delims=." %%a in ("%version_actual%") do (

    set major=%%a

    set minor=%%b

    set patch=%%c

)
 
set /a patch=patch + 1

set nueva_version=%major%.%minor%.%patch%
 
:: Actualizar archivo version

(

    echo %nueva_version%

    echo %fecha%

) > version
 
:: Agregar cambios

echo Agregando todos los cambios al repositorio...

git add .

if errorlevel 1 (

    echo Error al agregar archivos con git add.

    exit /b 1

)
 
git commit -m "despliegue realizado el %fecha% con versión %nueva_version%"

if errorlevel 1 (

    echo Error al hacer commit con git commit.

    exit /b 1

)
 
:: Borrar ZIP y carpeta

if exist deploy.zip (

    echo Eliminando deploy.zip...

    del /f /q deploy.zip

)
 
if exist deploy (

    echo Eliminando carpeta deploy...

    rmdir /s /q deploy

)
 
:: Crear nuevo archivo deploy.zip

echo Creando deploy.zip desde Git HEAD...

git archive -o deploy.zip HEAD
 
:: Añadir .env al ZIP (requiere PowerShell 5+)

echo Añadiendo .env a deploy.zip...

powershell -Command "Add-Type -Assembly 'System.IO.Compression.FileSystem'; $zip = [System.IO.Compression.ZipFile]::Open('deploy.zip', 'Update'); [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, '.env', '.env'); $zip.Dispose()"
 
:: Extraer deploy.zip a carpeta deploy

echo Extrayendo contenido a carpeta deploy...

powershell -Command "Expand-Archive -Path 'deploy.zip' -DestinationPath 'deploy' -Force"
 
echo Artefacto para despliegue completado con versión %nueva_version%.

endlocal
 
