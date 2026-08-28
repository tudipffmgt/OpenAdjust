import { ref } from 'vue'

// Modul-Singleton: nur EINE Pyodide-Instanz für die ganze App
let pyodidePromise = null

// Reaktiver Status – damit die GUI einen Ladebildschirm zeigen kann
export const pyodideStatus = ref('idle')  // idle | loading | ready | error

async function _initPyodide() {
  pyodideStatus.value = 'loading'

  // loadPyodide kommt aus dem CDN-Script in index.html (global auf window)
  const pyodide = await window.loadPyodide()

  await pyodide.loadPackage(['numpy', 'scipy', 'micropip'])

  const micropip = pyodide.pyimport('micropip')
  await micropip.install(
    `${import.meta.env.BASE_URL}openadjust-0.1.0-py3-none-any.whl`,
    { keepGoing: true, deps: false }
  )

  // Bootstrap-Python laden und ausführen
  const bootstrap =   const bootstrap = await (await fetch(`${import.meta.env.BASE_URL}py/bootstrap.py`)).text()
  await pyodide.runPythonAsync(bootstrap)

  pyodideStatus.value = 'ready'
  return pyodide
}

/** Liefert die (einmalig initialisierte) Pyodide-Instanz. */
export function usePyodide() {
  if (!pyodidePromise) {
    pyodidePromise = _initPyodide().catch(err => {
      pyodideStatus.value = 'error'
      pyodidePromise = null   // erlaubt erneuten Versuch nach Fehler
      throw err
    })
  }
  return pyodidePromise
}
