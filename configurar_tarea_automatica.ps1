# Script para crear tarea programada en Windows Task Scheduler
# Ejecuta el pipeline completo cada 3 horas

$TaskName = "TEMPO_Data_Pipeline"
$ScriptPath = "C:\Users\Sebastian\Desktop\TEMPO_Data\pipeline_completo.py"
$PythonPath = python -c "import sys; print(sys.executable)"
$WorkingDir = "C:\Users\Sebastian\Desktop\TEMPO_Data"

# Verificar que existan los archivos
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Error: No se encuentra pipeline_completo.py" -ForegroundColor Red
    exit 1
}

Write-Host "="*70 -ForegroundColor Cyan
Write-Host "🗓️  Configurando tarea programada de Windows" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Tarea: $TaskName" -ForegroundColor Yellow
Write-Host "Script: $ScriptPath" -ForegroundColor Yellow
Write-Host "Python: $PythonPath" -ForegroundColor Yellow
Write-Host "Frecuencia: Cada 3 horas" -ForegroundColor Yellow
Write-Host ""

# Eliminar tarea existente si existe
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "⚠️  Tarea existente encontrada. Eliminando..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Crear acción (ejecutar Python script)
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Crear trigger (cada 3 horas, comenzando ahora)
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 3)

# Configuración de la tarea
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Registrar la tarea
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Descarga y procesa datos TEMPO cada 3 horas automáticamente" `
        -User $env:USERNAME `
        -RunLevel Limited
    
    Write-Host "✅ Tarea programada creada exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Detalles de la tarea:" -ForegroundColor Cyan
    Write-Host "   • Se ejecutará cada 3 horas" -ForegroundColor White
    Write-Host "   • Primera ejecución: Ahora" -ForegroundColor White
    Write-Host "   • Timeout máximo: 1 hora" -ForegroundColor White
    Write-Host "   • Funciona aunque esté en batería" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Comandos útiles:" -ForegroundColor Cyan
    Write-Host "   Ver estado:" -ForegroundColor Yellow
    Write-Host "     Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "   Ejecutar ahora:" -ForegroundColor Yellow
    Write-Host "     Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "   Deshabilitar:" -ForegroundColor Yellow
    Write-Host "     Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "   Eliminar:" -ForegroundColor Yellow
    Write-Host "     Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📊 También puedes ver la tarea en:" -ForegroundColor Cyan
    Write-Host "   Task Scheduler > Biblioteca del Programador de tareas" -ForegroundColor White
    Write-Host ""
    
    # Preguntar si quiere ejecutar ahora
    $response = Read-Host "¿Quieres ejecutar el pipeline AHORA para probar? (S/N)"
    if ($response -eq 'S' -or $response -eq 's') {
        Write-Host "`n🚀 Ejecutando pipeline..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "✅ Pipeline iniciado. Verifica los logs." -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Error al crear la tarea: $_" -ForegroundColor Red
    exit 1
}
