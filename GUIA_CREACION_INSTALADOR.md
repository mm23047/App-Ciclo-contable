# 🔧 Guía para Desarrolladores: Crear Instalador Ejecutable

## Sistema Contable Empresarial

> **Objetivo:** Generar un instalador .exe portable que permita a estudiantes instalar y usar el sistema con un solo clic.

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Creación de Scripts Auxiliares](#creación-de-scripts-auxiliares)
4. [Configuración de Inno Setup](#configuración-de-inno-setup)
5. [Recursos Visuales](#recursos-visuales)
6. [Compilación del Instalador](#compilación-del-instalador)
7. [Testing y Distribución](#testing-y-distribución)
8. [Troubleshooting](#troubleshooting)

---

## 🛠️ Requisitos Previos

### Software Necesario

| Software               | Versión | Descarga                                          | Propósito                |
| ---------------------- | ------- | ------------------------------------------------- | ------------------------ |
| **Inno Setup**         | 6.x+    | [jrsoftware.org](https://jrsoftware.org/isdl.php) | Crear instalador Windows |
| **Docker Desktop**     | 4.0+    | Ya instalado                                      | Verificar funcionamiento |
| **Git**                | 2.30+   | Ya instalado                                      | Control de versiones     |
| **Editor de Imágenes** | -       | GIMP/Photoshop                                    | Crear iconos .ico y .bmp |

### Verificar Instalaciones

```bash
# Verificar versiones
docker --version
git --version

# Verificar Inno Setup
dir "C:\Program Files (x86)\Inno Setup 6"
```

---

## 📁 Estructura del Proyecto

### Crear Carpeta del Instalador

```bash
# Desde la raíz del proyecto
cd C:\Users\MINED\Documents\Sistema-contable-proyecto-de-ciclo

# Crear estructura
mkdir InstaladorPortable
cd InstaladorPortable
mkdir assets
mkdir dependencias
mkdir proyecto
mkdir scripts
mkdir output
```

### Estructura Completa

```
Sistema-contable-proyecto-de-ciclo/
│
├── BE/                                  # Backend (ya existe)
├── FE/                                  # Frontend (ya existe)
├── docker-compose.yml                   # Orquestación (ya existe)
├── .env                                 # Variables de entorno (ya existe)
├── README.md                            # Documentación principal (ya existe)
├── GUIA_INSTALACION_ESTUDIANTES.md     # Guía para estudiantes (ya existe)
│
└── InstaladorPortable/                  # NUEVA CARPETA
    │
    ├── assets/                          # Recursos visuales
    │   ├── icono_app.ico               # 256x256px - Icono principal
    │   ├── banner_instalador.bmp       # 164x314px - Banner lateral
    │   └── logo_sistema.bmp            # 55x58px - Logo pequeño
    │
    ├── dependencias/                    # Instaladores externos
    │   └── DockerDesktopInstaller.exe  # Se descarga automáticamente
    │
    ├── proyecto/                        # Copia del proyecto completo
    │   ├── BE/
    │   ├── FE/
    │   ├── docker-compose.yml
    │   ├── .env
    │   └── README.md
    │
    ├── scripts/                         # Scripts de automatización
    │   ├── iniciar.bat                 # Launcher principal
    │   ├── detener.bat                 # Detener servicios
    │   └── verificar_docker.bat        # Validación de Docker
    │
    ├── output/                          # Instalador compilado (generado)
    │   └── SistemaContable_Instalador_v1.0.0.exe
    │
    └── instalador.iss                   # Script de Inno Setup (PRINCIPAL)
```

---

## 📝 Creación de Scripts Auxiliares

### Script 1: `scripts/iniciar.bat`

```batch
@echo off
:: Script de inicialización del Sistema Contable
title Sistema Contable - Iniciando
color 0A
cls

echo ========================================
echo   SISTEMA CONTABLE EMPRESARIAL
echo ========================================
echo.
echo [1/4] Verificando Docker...

:: Verificar Docker instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker no esta instalado.
    echo.
    echo Por favor, ejecute nuevamente el instalador.
    pause
    exit /b 1
)

echo [OK] Docker encontrado
echo.
echo [2/4] Iniciando Docker Desktop...

:: Verificar si Docker Desktop está corriendo
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    :: Iniciar Docker Desktop
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Esperando que Docker inicie (puede tardar 30-60 segundos)...

    :: Esperar hasta que Docker esté listo
    :esperar_docker
    timeout /t 5 /nobreak >nul
    docker ps >nul 2>&1
    if %errorlevel% neq 0 goto esperar_docker
)

echo [OK] Docker activo
echo.
echo [3/4] Iniciando servicios del sistema...

:: Cambiar al directorio de la aplicación
cd /d "%~dp0.."

:: Levantar contenedores
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron iniciar los servicios
    echo.
    echo Revise los logs con: docker-compose logs
    pause
    exit /b 1
)

echo [OK] Servicios iniciados
echo.
echo [4/4] Abriendo navegador...

:: Esperar que los servicios estén completamente listos
timeout /t 10 /nobreak >nul

:: Abrir navegador
start http://localhost:8501

cls
echo ========================================
echo   SISTEMA INICIADO CORRECTAMENTE
echo ========================================
echo.
echo  Accede en: http://localhost:8501
echo.
echo  Credenciales:
echo    Usuario:    admin
echo    Contrasena: admin123
echo.
echo ========================================
echo.
echo [INFO] Manten esta ventana abierta
echo [INFO] Para detener: Ejecuta DETENER
echo.
echo Presiona cualquier tecla para ver logs...
pause >nul

:: Mostrar logs en tiempo real (opcional)
docker-compose logs -f
```

### Script 2: `scripts/detener.bat`

```batch
@echo off
:: Script para detener el Sistema Contable
title Sistema Contable - Deteniendo
color 0C
cls

echo ========================================
echo   DETENIENDO SISTEMA CONTABLE
echo ========================================
echo.

:: Cambiar al directorio de la aplicación
cd /d "%~dp0.."

echo Deteniendo contenedores...
docker-compose down

if %errorlevel% equ 0 (
    echo.
    echo [OK] Sistema detenido correctamente.
    echo.
    echo Los datos se han guardado y estaran disponibles
    echo la proxima vez que inicie el sistema.
) else (
    echo.
    echo [ERROR] Hubo un problema al detener el sistema.
    echo.
    echo Intente cerrar Docker Desktop manualmente.
)

echo.
pause
```

### Script 3: `scripts/verificar_docker.bat`

```batch
@echo off
:: Script silencioso para verificar Docker
docker --version >nul 2>&1
exit /b %errorlevel%
```

---

## ⚙️ Configuración de Inno Setup

### Archivo Principal: `instalador.iss`

Este es el archivo más importante. Créalo en la raíz de `InstaladorPortable/`:

```pascal
; ============================================
; SISTEMA CONTABLE EMPRESARIAL
; Script de Inno Setup para Instalador Portable
; ============================================

; Definiciones básicas
#define NombreApp "Sistema Contable Empresarial"
#define Version "1.0.0"
#define Editor "Tu Nombre o Institución"
#define URLApp "https://github.com/mm23047/App-Ciclo-contable"
#define ArchivoEjecutable "iniciar.bat"

[Setup]
; Identificador único (generar en https://guidgenerator.com/)
AppId={{12345678-ABCD-1234-ABCD-1234567890AB}}

; Información de la aplicación
AppName={#NombreApp}
AppVersion={#Version}
AppPublisher={#Editor}
AppPublisherURL={#URLApp}
AppSupportURL={#URLApp}/issues
AppUpdatesURL={#URLApp}/releases

; Directorios
DefaultDirName={autopf}\{#NombreApp}
DefaultGroupName={#NombreApp}
AllowNoIcons=yes

; Archivos de configuración
LicenseFile=..\LICENSE
InfoBeforeFile=..\GUIA_INSTALACION_ESTUDIANTES.md
OutputDir=output
OutputBaseFilename=SistemaContable_Instalador_v{#Version}

; Iconos y apariencia
SetupIconFile=assets\icono_app.ico
WizardImageFile=assets\banner_instalador.bmp
WizardSmallImageFile=assets\logo_sistema.bmp

; Compresión
Compression=lzma2/ultra64
SolidCompression=yes

; Estilo
WizardStyle=modern

; Permisos y arquitectura
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el &escritorio"; GroupDescription: "Iconos adicionales:"
Name: "startmenuicon"; Description: "Crear icono en menú &Inicio"; GroupDescription: "Iconos adicionales:"
Name: "instalardocker"; Description: "Instalar Docker Desktop (requerido si no está instalado)"; GroupDescription: "Componentes requeridos:"; Check: NecesitaDocker

[Files]
; Copiar aplicación completa
Source: "proyecto\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Copiar scripts auxiliares
Source: "scripts\iniciar.bat"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\detener.bat"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\verificar_docker.bat"; DestDir: "{app}\scripts"; Flags: ignoreversion

; Copiar iconos para los scripts
Source: "assets\icono_app.ico"; DestDir: "{app}\scripts"; Flags: ignoreversion

; Instalador de Docker (descarga externa)
Source: "dependencias\DockerDesktopInstaller.exe"; DestDir: "{tmp}"; Flags: external deleteafterinstall; Check: NecesitaDocker; Tasks: instalardocker

[Icons]
; Icono en menú Inicio
Name: "{group}\{#NombreApp}"; Filename: "{app}\scripts\iniciar.bat"; IconFilename: "{app}\scripts\icono_app.ico"; WorkingDir: "{app}"
Name: "{group}\Detener {#NombreApp}"; Filename: "{app}\scripts\detener.bat"; IconFilename: "{app}\scripts\icono_app.ico"; WorkingDir: "{app}"
Name: "{group}\Manual de Usuario"; Filename: "{app}\GUIA_INSTALACION_ESTUDIANTES.md"
Name: "{group}\Desinstalar {#NombreApp}"; Filename: "{uninstallexe}"

; Icono en escritorio
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\scripts\iniciar.bat"; IconFilename: "{app}\scripts\icono_app.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Instalar Docker Desktop si es necesario
Filename: "{tmp}\DockerDesktopInstaller.exe"; Parameters: "install --quiet"; StatusMsg: "Instalando Docker Desktop (puede tardar varios minutos)..."; Flags: waituntilterminated; Check: NecesitaDocker; Tasks: instalardocker

; Ofrecer iniciar la aplicación al finalizar
Filename: "{app}\scripts\iniciar.bat"; Description: "Iniciar {#NombreApp} ahora"; Flags: postinstall nowait skipifsilent; Check: not NecesitaDocker

[UninstallRun]
; Detener servicios al desinstalar
Filename: "{app}\scripts\detener.bat"; RunOnceId: "DetenerServicios"

[UninstallDelete]
; Limpiar archivos generados
Type: filesandordirs; Name: "{app}"

[Code]
var
  PaginaDescargaDocker: TDownloadWizardPage;
  NecesitaReiniciar: Boolean;

// ============================================
// FUNCIONES DE VALIDACIÓN
// ============================================

// Verificar si Docker está instalado
function DockerEstaInstalado: Boolean;
var
  ResultCode: Integer;
begin
  Result := FileExists('C:\Program Files\Docker\Docker\Docker Desktop.exe') or
            FileExists(ExpandConstant('{pf}\Docker\Docker\Docker Desktop.exe'));
end;

// Verificar si necesita instalar Docker
function NecesitaDocker: Boolean;
begin
  Result := not DockerEstaInstalado;
end;

// Verificar requisitos del sistema
function VerificarRequisitos: Boolean;
var
  RAMSize: Cardinal;
  Version: TWindowsVersion;
begin
  Result := True;
  GetWindowsVersionEx(Version);

  // Verificar Windows 10/11 de 64 bits
  if not IsWin64 then
  begin
    MsgBox('Este sistema requiere Windows de 64 bits.' + #13#10 +
           'Tu sistema es de 32 bits y no es compatible.',
           mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Verificar versión de Windows
  if (Version.Major < 10) then
  begin
    MsgBox('Este sistema requiere Windows 10 o superior.' + #13#10 +
           'Tu versión de Windows no es compatible.',
           mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Verificar RAM (mínimo 4GB)
  RAMSize := GetTotalPhysMemory div (1024 * 1024);
  if RAMSize < 4096 then
  begin
    if MsgBox('ADVERTENCIA: Tu computadora tiene ' + IntToStr(RAMSize) + ' MB de RAM.' + #13#10 +
              'Se recomienda al menos 4096 MB (4GB) para un funcionamiento óptimo.' + #13#10 + #13#10 +
              '¿Deseas continuar de todos modos?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

// ============================================
// INICIALIZACIÓN DEL ASISTENTE
// ============================================

procedure InitializeWizard();
var
  InfoPage: TOutputMsgMemoWizardPage;
begin
  NecesitaReiniciar := False;

  // Crear página de información importante
  InfoPage := CreateOutputMsgMemoPage(wpWelcome,
    'Información Importante',
    'Por favor lee la siguiente información antes de continuar',
    'Este instalador configurará el Sistema Contable Empresarial en tu computadora.' + #13#10 + #13#10 +
    'REQUISITOS:' + #13#10 +
    '• Windows 10/11 de 64 bits' + #13#10 +
    '• 4GB de RAM mínimo' + #13#10 +
    '• 5GB de espacio en disco' + #13#10 +
    '• Docker Desktop (se instalará automáticamente si no lo tienes)' + #13#10 + #13#10 +
    'TIEMPO DE INSTALACIÓN:' + #13#10 +
    '• 5-15 minutos (dependiendo de si necesitas instalar Docker)' + #13#10 + #13#10 +
    'NOTA: Si se instala Docker Desktop, deberás reiniciar tu computadora.',
    '');

  // Crear página de descarga de Docker si es necesario
  if NecesitaDocker then
  begin
    PaginaDescargaDocker := CreateDownloadPage(
      'Descargando Docker Desktop',
      'El sistema está descargando Docker Desktop...',
      nil);
  end;
end;

// ============================================
// VALIDACIÓN INICIAL
// ============================================

function InitializeSetup(): Boolean;
begin
  Result := VerificarRequisitos;

  if not Result then
    Exit;

  // Advertir sobre Docker si no está instalado
  if NecesitaDocker then
  begin
    MsgBox('Docker Desktop no está instalado en tu sistema.' + #13#10 + #13#10 +
           'El instalador descargará e instalará Docker Desktop automáticamente.' + #13#10 +
           'Esto puede tardar 5-10 minutos adicionales.' + #13#10 + #13#10 +
           'IMPORTANTE: Deberás reiniciar tu computadora después de la instalación.',
           mbInformation, MB_OK);
  end;
end;

// ============================================
// NAVEGACIÓN ENTRE PÁGINAS
// ============================================

function NextButtonClick(CurPageID: Integer): Boolean;
var
  URLDocker: String;
begin
  Result := True;

  // Descargar Docker Desktop si es necesario
  if (CurPageID = wpReady) and NecesitaDocker and WizardIsTaskSelected('instalardocker') then
  begin
    URLDocker := 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe';

    PaginaDescargaDocker.Clear;
    PaginaDescargaDocker.Add(URLDocker, 'DockerDesktopInstaller.exe', '');
    PaginaDescargaDocker.Show;

    try
      PaginaDescargaDocker.Download;
      Result := True;
      NecesitaReiniciar := True;
    except
      if PaginaDescargaDocker.AbortedByUser then
      begin
        MsgBox('La descarga fue cancelada.' + #13#10 +
               'Docker Desktop es necesario para que el sistema funcione.',
               mbInformation, MB_OK);
        Result := False;
      end
      else
      begin
        MsgBox('Error al descargar Docker Desktop: ' + AddPeriod(GetExceptionMessage),
               mbError, MB_OK);
        Result := False;
      end;
    end;
  end;
end;

// ============================================
// POST-INSTALACIÓN
// ============================================

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Crear archivo de configuración .env si no existe
    if not FileExists(ExpandConstant('{app}\.env')) then
    begin
      SaveStringToFile(ExpandConstant('{app}\.env'),
        'PORT_BE=8000' + #13#10 +
        'PORT_FE=8501' + #13#10 +
        'POSTGRES_USER=postgres' + #13#10 +
        'POSTGRES_PASSWORD=abc123' + #13#10 +
        'POSTGRES_DB=zapateria' + #13#10 +
        'POSTGRES_HOST=sistema_contable_db' + #13#10 +
        'POSTGRES_PORT=5432' + #13#10 +
        'PGADMIN_EMAIL=admin@admin.com' + #13#10 +
        'PGADMIN_PASSWORD=abc123' + #13#10 +
        'PGADMIN_PORT=5050',
        False);
    end;
  end;
end;

// ============================================
// FINALIZACIÓN
// ============================================

procedure DeinitializeSetup();
var
  ResultCode: Integer;
begin
  if NecesitaReiniciar then
  begin
    if MsgBox('La instalación ha finalizado correctamente.' + #13#10 + #13#10 +
              'IMPORTANTE: Debes reiniciar tu computadora para completar ' +
              'la instalación de Docker Desktop.' + #13#10 + #13#10 +
              '¿Deseas reiniciar ahora?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec('shutdown', '/r /t 10 /c "Reiniciando para completar instalación de Docker Desktop"',
           '', SW_SHOW, ewNoWait, ResultCode);
    end
    else
    begin
      MsgBox('Recuerda reiniciar tu computadora antes de usar el sistema.',
             mbInformation, MB_OK);
    end;
  end
  else
  begin
    // Mostrar mensaje de éxito
    MsgBox('¡Instalación completada exitosamente!' + #13#10 + #13#10 +
           'Para iniciar el sistema:' + #13#10 +
           '1. Haz doble clic en el icono del escritorio' + #13#10 +
           '2. Espera 1-2 minutos mientras inicia' + #13#10 +
           '3. Se abrirá automáticamente en tu navegador' + #13#10 + #13#10 +
           'Credenciales de acceso:' + #13#10 +
           '  Usuario: admin' + #13#10 +
           '  Contraseña: admin123',
           mbInformation, MB_OK);
  end;
end;

// ============================================
// DESINSTALACIÓN
// ============================================

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    if MsgBox('¿Deseas detener y eliminar los contenedores de Docker del sistema?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec('cmd.exe',
           '/c cd /d "' + ExpandConstant('{app}') + '" && docker-compose down -v',
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
```

---

## 🎨 Recursos Visuales

### Iconos Requeridos

Necesitas crear 3 archivos de imagen:

#### 1. `assets/icono_app.ico` (256x256 píxeles)

**Herramientas para crear:**

- **Online (Recomendado):** [icoconvert.com](https://icoconvert.com/)
- **Software:** GIMP, Photoshop, Illustrator

**Proceso:**

```bash
1. Diseña un logo de 256x256px en formato PNG
2. Sube a icoconvert.com
3. Descarga el archivo .ico generado
4. Guarda como: InstaladorPortable/assets/icono_app.ico
```

#### 2. `assets/banner_instalador.bmp` (164x314 píxeles)

**Dimensiones:** 164px ancho × 314px alto  
**Formato:** BMP (Bitmap)

**Proceso:**

```bash
1. Crea una imagen vertical con tu diseño
2. Puede incluir: logo, nombre del sistema, elementos decorativos
3. Guarda como BMP: InstaladorPortable/assets/banner_instalador.bmp
```

#### 3. `assets/logo_sistema.bmp` (55x58 píxeles)

**Dimensiones:** 55px ancho × 58px alto  
**Formato:** BMP (Bitmap)

**Proceso:**

```bash
1. Crea un logo pequeño cuadrado
2. Guarda como BMP: InstaladorPortable/assets/logo_sistema.bmp
```

### Plantillas de Colores Recomendadas

```
Esquema Contable Profesional:
- Color Principal: #2C3E50 (Azul oscuro)
- Color Secundario: #3498DB (Azul claro)
- Color Acento: #E74C3C (Rojo)
- Fondo: #ECF0F1 (Gris claro)
```

---

## 🏗️ Compilación del Instalador

### Paso 1: Preparar el Proyecto

```bash
# Ir a la raíz del proyecto
cd C:\Users\MINED\Documents\Sistema-contable-proyecto-de-ciclo

# Copiar proyecto completo a la carpeta del instalador
xcopy /E /I /Y BE InstaladorPortable\proyecto\BE
xcopy /E /I /Y FE InstaladorPortable\proyecto\FE
copy docker-compose.yml InstaladorPortable\proyecto\
copy .env InstaladorPortable\proyecto\
copy README.md InstaladorPortable\proyecto\
copy GUIA_INSTALACION_ESTUDIANTES.md InstaladorPortable\proyecto\
copy insert_periodos_pgadmin.sql InstaladorPortable\proyecto\

# Limpiar archivos innecesarios
rd /S /Q InstaladorPortable\proyecto\BE\__pycache__
rd /S /Q InstaladorPortable\proyecto\FE\__pycache__
rd /S /Q InstaladorPortable\proyecto\.git
```

### Paso 2: Verificar Estructura

```bash
# Verificar que todos los archivos estén en su lugar
dir InstaladorPortable\assets
dir InstaladorPortable\scripts
dir InstaladorPortable\proyecto
dir InstaladorPortable\instalador.iss
```

### Paso 3: Compilar con Inno Setup

#### Método 1: Interfaz Gráfica

```
1. Abrir "Inno Setup Compiler"
2. File → Open
3. Seleccionar: InstaladorPortable\instalador.iss
4. Build → Compile (o presionar F9)
5. Esperar 5-10 minutos
6. ¡Listo! El instalador está en: InstaladorPortable\output\
```

#### Método 2: Línea de Comandos

```bash
# Desde CMD o PowerShell
cd C:\Users\MINED\Documents\Sistema-contable-proyecto-de-ciclo\InstaladorPortable

# Compilar
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss

# Verificar salida
dir output\
```

### Paso 4: Verificar el Instalador Generado

```bash
# Debería existir:
InstaladorPortable\output\SistemaContable_Instalador_v1.0.0.exe

# Verificar tamaño (aproximadamente 500MB - 1GB)
dir InstaladorPortable\output\

# Propiedades esperadas:
# - Nombre: SistemaContable_Instalador_v1.0.0.exe
# - Tamaño: ~500MB - 1GB
# - Icono: Tu icono personalizado visible
```

---

## 🧪 Testing y Distribución

### Testing Local

#### Test 1: Instalación en Máquina Limpia (Recomendado)

**Usando Windows Sandbox (Windows 10 Pro/Enterprise):**

```bash
# 1. Habilitar Windows Sandbox
# Panel de Control → Programas → Activar o desactivar características de Windows
# Marcar "Windows Sandbox"

# 2. Iniciar Windows Sandbox

# 3. Copiar instalador a Sandbox

# 4. Ejecutar instalador y verificar:
# - Instalación completa sin errores
# - Docker se instala correctamente
# - Sistema inicia correctamente
# - Todos los módulos funcionan
```

**Usando Máquina Virtual (VirtualBox/VMware):**

```bash
# 1. Crear VM con Windows 10/11 limpio
# 2. Configurar VM: 4GB RAM, 50GB disco
# 3. Copiar instalador a VM
# 4. Probar instalación completa
# 5. Verificar funcionamiento
```

#### Test 2: Verificación Funcional

**Checklist de pruebas:**

```
✓ El instalador se ejecuta sin errores
✓ Docker Desktop se instala (si no estaba)
✓ Todos los archivos se copian correctamente
✓ Los iconos aparecen en escritorio y menú inicio
✓ Al hacer doble clic en "Sistema Contable":
  ✓ Se inicia Docker Desktop
  ✓ Se levantan los contenedores
  ✓ Se abre el navegador automáticamente
  ✓ El sistema carga correctamente
✓ Se puede hacer login con admin/admin123
✓ Todos los módulos son accesibles
✓ Se pueden crear cuentas, transacciones, facturas
✓ Al ejecutar "Detener", los contenedores se detienen
✓ La desinstalación funciona correctamente
```

### Distribución

#### Opción 1: Distribución por USB

```bash
# Crear paquete para USB
mkdir Distribucion_USB
cd Distribucion_USB

# Copiar instalador
copy ..\InstaladorPortable\output\SistemaContable_Instalador_v1.0.0.exe .

# Crear archivo README.txt
echo SISTEMA CONTABLE EMPRESARIAL > README.txt
echo ============================ >> README.txt
echo. >> README.txt
echo Para instalar: >> README.txt
echo 1. Haz doble clic en SistemaContable_Instalador_v1.0.0.exe >> README.txt
echo 2. Sigue las instrucciones en pantalla >> README.txt
echo 3. Espera a que termine (5-15 minutos) >> README.txt
echo. >> README.txt
echo Para mas informacion, consulta GUIA_INSTALACION_ESTUDIANTES.md >> README.txt

# Copiar guía de estudiantes
copy ..\GUIA_INSTALACION_ESTUDIANTES.md .

# Comprimir todo en ZIP (opcional)
powershell Compress-Archive -Path * -DestinationPath SistemaContable_USB.zip
```

#### Opción 2: Distribución por Google Drive

```bash
# 1. Subir a Google Drive:
#    - SistemaContable_Instalador_v1.0.0.exe
#    - GUIA_INSTALACION_ESTUDIANTES.md

# 2. Obtener link compartido

# 3. Compartir con estudiantes
```

#### Opción 3: Servidor de la Institución

```bash
# Subir al servidor FTP/HTTP de la institución
# Los estudiantes descargan desde red local (más rápido)
```

---

## 🔧 Troubleshooting

### Problemas Comunes al Compilar

#### Error: "Cannot find assets/icono_app.ico"

**Causa:** Falta el archivo de icono

**Solución:**

```bash
# Verificar que exista
dir InstaladorPortable\assets\icono_app.ico

# Si no existe, crear uno o comentar la línea en instalador.iss:
# ;SetupIconFile=assets\icono_app.ico
```

#### Error: "Syntax error in line X"

**Causa:** Error de sintaxis en instalador.iss

**Solución:**

```bash
# Verificar la línea indicada
# Buscar:
#   - Comillas mal cerradas
#   - Punto y coma faltantes
#   - Paréntesis desbalanceados
```

#### Error: "Cannot copy files"

**Causa:** Rutas incorrectas a los archivos fuente

**Solución:**

```bash
# Verificar que proyecto/ tenga todo:
dir InstaladorPortable\proyecto\BE
dir InstaladorPortable\proyecto\FE
dir InstaladorPortable\proyecto\docker-compose.yml
```

### Problemas al Probar el Instalador

#### El instalador no se ejecuta

**Causa:** Windows Defender o antivirus lo bloquea

**Solución:**

```bash
# 1. Click derecho en el .exe
# 2. Propiedades
# 3. Desbloquear
# 4. O agregar excepción en Windows Defender
```

#### Docker no se instala correctamente

**Causa:** Virtualización deshabilitada en BIOS

**Solución:**

```bash
# Usuario debe:
# 1. Reiniciar PC
# 2. Entrar a BIOS (F2/F10/DEL)
# 3. Habilitar "Virtualization Technology" o "VT-x"
# 4. Guardar y reiniciar
```

---

## 📊 Optimización del Instalador

### Reducir Tamaño del Instalador

```bash
# Excluir archivos innecesarios antes de compilar

# Eliminar node_modules si existen
rd /S /Q InstaladorPortable\proyecto\FE\node_modules

# Eliminar __pycache__
for /d /r InstaladorPortable\proyecto %d in (__pycache__) do @if exist "%d" rd /s /q "%d"

# Eliminar archivos .pyc
del /S /Q InstaladorPortable\proyecto\*.pyc

# Eliminar .git
rd /S /Q InstaladorPortable\proyecto\.git

# Eliminar logs
del /S /Q InstaladorPortable\proyecto\*.log
```

### Firma Digital (Opcional pero Recomendado)

```bash
# Para evitar advertencias de Windows SmartScreen

# Necesitas certificado de firma de código
# Proveedores: Sectigo, DigiCert, GlobalSign (~$100-300/año)

# Comando para firmar:
signtool sign /f "MiCertificado.pfx" /p "ContraseñaCertificado" /tr http://timestamp.digicert.com /td sha256 /fd sha256 "InstaladorPortable\output\SistemaContable_Instalador_v1.0.0.exe"
```

---

## 📋 Checklist Final

### Antes de Distribuir

```
✓ Compilación exitosa sin errores
✓ Probado en máquina limpia (VM o Sandbox)
✓ Todos los módulos funcionan correctamente
✓ Iconos visibles y correctos
✓ Documentación incluida (GUIA_INSTALACION_ESTUDIANTES.md)
✓ Tamaño del instalador razonable (~500MB-1GB)
✓ Archivo README.txt creado para USB
✓ Links de descarga funcionando (si aplica)
✓ Instrucciones claras para estudiantes
✓ Contacto de soporte definido
```

---

## 📚 Recursos Adicionales

### Enlaces Útiles

| Recurso                      | URL                                            |
| ---------------------------- | ---------------------------------------------- |
| **Inno Setup Documentación** | https://jrsoftware.org/ishelp/                 |
| **Inno Setup Ejemplos**      | https://jrsoftware.org/isinfo.php              |
| **Generador de GUID**        | https://guidgenerator.com/                     |
| **Conversor ICO**            | https://icoconvert.com/                        |
| **Docker Desktop**           | https://www.docker.com/products/docker-desktop |

### Comandos Útiles

```bash
# Ver logs de compilación de Inno Setup
type "%TEMP%\InnoSetup.log"

# Verificar instalador sin instalarlo
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /? instalador.iss

# Crear instalador silencioso (sin GUI)
SistemaContable_Instalador_v1.0.0.exe /SILENT

# Crear instalador muy silencioso (sin ninguna UI)
SistemaContable_Instalador_v1.0.0.exe /VERYSILENT
```

---

## 🎯 Resumen Rápido

### Para Crear el Instalador:

```bash
# 1. Instalar Inno Setup
# 2. Crear estructura InstaladorPortable/
# 3. Crear scripts .bat
# 4. Crear instalador.iss
# 5. Crear iconos .ico y .bmp
# 6. Copiar proyecto completo
# 7. Compilar con Inno Setup (F9)
# 8. Probar en máquina limpia
# 9. Distribuir a estudiantes
```

### Resultado Final:

```
Un archivo .exe de ~500MB-1GB que:
✓ Instala Docker automáticamente si es necesario
✓ Copia toda la aplicación
✓ Crea iconos en escritorio y menú inicio
✓ Permite iniciar el sistema con un doble clic
✓ Es fácil de desinstalar
✓ No requiere conocimientos técnicos del usuario
```

---

**Última actualización:** 11 de Diciembre de 2025  
**Versión de la guía:** 1.0  
**Mantenedor:** [Tu Nombre]

---

_¿Encontraste algún error o tienes sugerencias? Actualiza este documento con tus mejoras._
