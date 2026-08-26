import { usePyodide } from '../composables/usePyodide'

/**
 * Gleicht ein Netz aus.
 * @param {object} networkDict - Netz als plain dict (dein .oadj-Schema)
 * @returns {Promise<object>} Ergebnis-Dict (aus result_to_dict)
 */
export async function adjustNetwork(networkDict) {
  const pyodide = await usePyodide()

  // JS -> Python über JSON (robust, keine Proxy-Fallen)
  pyodide.globals.set('input_json', JSON.stringify(networkDict))

  const resultJson = await pyodide.runPythonAsync(`
import json
from openadjust.io.serialization import dict_to_network, result_to_dict
from openadjust.core.adjustment import LeastSquaresAdjustment

_net = dict_to_network(json.loads(input_json))
_res = LeastSquaresAdjustment(_net, verbose=False).run()
json.dumps(result_to_dict(_res))
`)

  return JSON.parse(resultJson)
}
