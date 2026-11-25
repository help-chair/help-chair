import { useCallback, useEffect, useState } from 'react'
import { cargarArticulosConRespaldo } from './api'
import type { Articulo, Valoracion } from './types'

// Estado del módulo: carga desde services/knowledge (con respaldo a datos de ejemplo)
// y mantiene las valoraciones en memoria hasta que el backend exponga esos endpoints.

export type EstadoCarga = 'cargando' | 'lista' | 'error'

export function useArticulos(cargar: () => Promise<Articulo[]> = cargarArticulosConRespaldo) {
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
