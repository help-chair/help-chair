import { useCallback, useEffect, useState } from 'react'
import { cargarArticulosDeEjemplo } from './data'
import type { Articulo, Valoracion } from './types'

// Estado del módulo en memoria (se pierde al recargar). Para conectarlo a services/knowledge,
// cambia el cuerpo de estas funciones por llamadas a la API en src/api/; los componentes no cambian.

export type EstadoCarga = 'cargando' | 'lista' | 'error'

export function useArticulos(cargar: () => Promise<Articulo[]> = cargarArticulosDeEjemplo) {
  const [carga, setCarga] = useState<EstadoCarga>('cargando')
  const [articulos, setArticulos] = useState<Articulo[]>([])
  const [valoraciones, setValoraciones] = useState<Valoracion[]>([])

  const recargar = useCallback(() => {
    let vigente = true
    setCarga('cargando')
    cargar().then(
      (nuevos) => {
        if (!vigente) return
        setArticulos(nuevos)
        setCarga('lista')
      },
      () => {
        if (vigente) setCarga('error')
      },
    )
    return () => {
      vigente = false
    }
  }, [cargar])

  useEffect(() => recargar(), [recargar])

  /** Suma una consulta cada vez que alguien abre el artículo. */
  function registrarConsulta(articuloId: string) {
    setArticulos((actual) =>
      actual.map((articulo) =>
        articulo.id === articuloId ? { ...articulo, consultas: articulo.consultas + 1 } : articulo,
      ),
    )
  }

  /** Respuesta a «¿Te resultó útil este artículo?», con comentario opcional si no sirvió. */
  function valorar(valoracion: Valoracion) {
    setValoraciones((actual) => [...actual, valoracion])
    setArticulos((actual) =>
      actual.map((articulo) =>
        articulo.id !== valoracion.articulo_id
          ? articulo
          : valoracion.util
            ? { ...articulo, votos_utiles: articulo.votos_utiles + 1 }
            : { ...articulo, votos_no_utiles: articulo.votos_no_utiles + 1 },
      ),
    )
  }

  return { carga, recargar, articulos, valoraciones, registrarConsulta, valorar }
}
