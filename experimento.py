"""Pruebas, datasets y benchmark reproducible: python experimento.py"""
import argparse
import csv
import ctypes
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import threading
import time
from lcs import VERSIONES, es_subsecuencia

BASE = Path(__file__).resolve().parent


def pico_memoria_mib():
    if os.name == 'nt':
        from ctypes import wintypes

        class Contadores(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),
                        ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t)]

        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Contadores), wintypes.DWORD]
        contadores = Contadores()
        contadores.cb = ctypes.sizeof(contadores)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(contadores), contadores.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return contadores.PeakWorkingSetSize / (1024 ** 2)
    import resource
    valor = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return valor / (1024 ** 2 if sys.platform == 'darwin' else 1024)


def trabajador(archivo, version, limite):
    datos = json.loads(Path(archivo).read_text(encoding='utf-8'))
    x, y = datos['x'], datos['y']
    inicio = time.process_time()
    bloqueo = threading.Lock()
    terminado = threading.Event()

    def vigilar():
        while not terminado.wait(0.01):
            transcurrido = time.process_time() - inicio
            if transcurrido >= limite:
                with bloqueo:
                    if terminado.is_set():
                        return
                    print(json.dumps({'estado': 'limite_cpu', 'cpu_observado_s': transcurrido,
                                      'pico_mib': pico_memoria_mib(), 'lcs': None}), flush=True)
                    os._exit(124)

    threading.Thread(target=vigilar, daemon=True).start()
    llamadas = 0
    while True:
        salida = VERSIONES[version](x, y)
        llamadas += 1
        transcurrido = time.process_time() - inicio
        if transcurrido >= 0.05:
            break
    with bloqueo:
        terminado.set()
        print(json.dumps({'estado': 'ok', 'cpu_s': transcurrido / llamadas,
                          'pico_mib': pico_memoria_mib(), 'llamadas': llamadas, 'lcs': salida}), flush=True)


def generar():
    directorio = BASE / 'datasets'
    directorio.mkdir(exist_ok=True)
    rng = random.Random(20261121)
    casos = []
    for n in [12, 16, 20, 64, 256, 1000]:
        for muestra in range(1, 4):
            caso = {'id': f'aleatorio_{n}_p{muestra}', 'tipo': 'aleatorio',
                    'm': n, 'n': n, 'muestra': muestra, 'alfabeto': 'ACGT',
                    'x': ''.join(rng.choices('ACGT', k=n)), 'y': ''.join(rng.choices('ACGT', k=n))}
            casos.append(caso)
    casos.append({'id': 'identicas_1000', 'tipo': 'control_identicas', 'm': 1000, 'n': 1000,
                  'x': 'A' * 1000, 'y': 'A' * 1000})
    casos.append({'id': 'disjuntas_1000', 'tipo': 'control_disjuntas', 'm': 1000, 'n': 1000,
                  'x': 'A' * 1000, 'y': 'B' * 1000})
    casos.append({'id': 'desiguales_1000_64', 'tipo': 'control_desiguales', 'm': 1000, 'n': 64,
                  'x': ''.join(rng.choices('ACGT', k=1000)), 'y': ''.join(rng.choices('ACGT', k=64))})
    alfabeto = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    casos.append({'id': 'alfabeto26_1000', 'tipo': 'control_alfabeto26', 'm': 1000, 'n': 1000,
                  'alfabeto': alfabeto, 'x': ''.join(rng.choices(alfabeto, k=1000)),
                  'y': ''.join(rng.choices(alfabeto, k=1000))})
    # Retirar únicamente las entradas generadas por la versión anterior del protocolo.
    for n in [12, 16, 20, 64, 1000]:
        (directorio / f'aleatorio_{n}.json').unlink(missing_ok=True)
    for caso in casos:
        (directorio / (caso['id'] + '.json')).write_text(json.dumps(caso, ensure_ascii=False, indent=2), encoding='utf-8')
    return casos


def ejecutar(repeticiones, limite_a):
    subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_lcs.py'], cwd=BASE, check=True)
    casos = generar()
    registros = []
    for caso in casos:
        for version in VERSIONES:
            for repeticion in range(1, repeticiones + 1):
                limite = limite_a if version == 'A' else 30.0
                comando = [sys.executable, str(Path(__file__).resolve()), '--worker',
                           str(BASE / 'datasets' / (caso['id'] + '.json')), version, '--limite-worker', str(limite)]
                proceso = subprocess.run(comando, capture_output=True, text=True, timeout=limite * 5 + 10)
                if proceso.returncode not in (0, 124):
                    raise RuntimeError(proceso.stderr or proceso.stdout)
                medicion = json.loads(proceso.stdout)
                if medicion['estado'] == 'ok':
                    salida = medicion['lcs']
                    assert es_subsecuencia(salida, caso['x']) and es_subsecuencia(salida, caso['y'])
                    medicion['longitud_lcs'] = len(salida)
                medicion.update(caso=caso['id'], tipo=caso['tipo'], m=caso['m'], n=caso['n'],
                                version=version, repeticion=repeticion)
                registros.append(medicion)
                print(caso['id'], version, repeticion, medicion['estado'], flush=True)
        longitudes = {r['longitud_lcs'] for r in registros if r['caso'] == caso['id'] and r['estado'] == 'ok'}
        assert len(longitudes) == 1, f'Desacuerdo en {caso["id"]}'
    resultados = BASE / 'resultados'
    resultados.mkdir(exist_ok=True)
    (resultados / 'mediciones.json').write_text(json.dumps(registros, indent=2, ensure_ascii=False), encoding='utf-8')
    resumen = []
    for caso in casos:
        for version in VERSIONES:
            filas = [r for r in registros if r['caso'] == caso['id'] and r['version'] == version]
            completadas = [r for r in filas if r['estado'] == 'ok']
            resumen.append({'caso': caso['id'], 'm': caso['m'], 'n': caso['n'], 'version': version,
                            'estado': ('ok' if len(completadas) == len(filas) else
                                       'parcial' if completadas else 'limite_cpu'),
                            'completadas': len(completadas), 'repeticiones': len(filas),
                            'cpu_mediana_s': statistics.median(r['cpu_s'] for r in completadas) if completadas else None,
                            'pico_max_mib': max(r['pico_mib'] for r in filas),
                            'longitud_lcs': completadas[0]['longitud_lcs'] if completadas else None})
    with (resultados / 'resumen.csv').open('w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resumen[0]))
        escritor.writeheader()
        escritor.writerows(resumen)
    entorno = {'python': sys.version, 'plataforma': platform.platform(), 'procesador': platform.processor(),
               'cpu_logicas': os.cpu_count(), 'repeticiones': repeticiones, 'limite_cpu_a_s': limite_a,
               'minimo_cpu_lote_s': 0.05, 'semilla': 20261121, 'alfabeto': 'ACGT',
               'parejas_aleatorias_por_longitud': 3, 'numero_casos': len(casos),
               'longitudes_aleatorias': [12, 16, 20, 64, 256, 1000],
               'memoria': 'Pico RSS/working set total del proceso; incluye intérprete y datos'}
    (resultados / 'entorno.json').write_text(json.dumps(entorno, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Resultados guardados en', resultados)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', nargs=2, metavar=('DATASET', 'VERSION'))
    parser.add_argument('--limite-worker', type=float, default=30)
    parser.add_argument('--repeticiones', type=int, default=3)
    parser.add_argument('--limite-a', type=float, default=1.5)
    args = parser.parse_args()
    if args.repeticiones < 1 or args.limite_a <= 0 or args.limite_worker <= 0:
        parser.error('Los límites y el número de repeticiones deben ser positivos.')
    if args.worker:
        trabajador(*args.worker, args.limite_worker)
    else:
        ejecutar(args.repeticiones, args.limite_a)
