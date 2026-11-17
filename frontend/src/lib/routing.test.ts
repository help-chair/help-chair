import { matchPath } from './routing'

describe('matchPath', () => {
  it('extrae parámetros', () => {
    expect(matchPath('/estado/:id', '/estado/abc-123')).toEqual({ id: 'abc-123' })
  })
  it('devuelve null si no coincide', () => {
    expect(matchPath('/estado/:id', '/registro')).toBeNull()
    expect(matchPath('/estado/:id', '/estado')).toBeNull()
  })
  it('ignora la barra final', () => {
    expect(matchPath('/registro', '/registro/')).toEqual({})
  })
})
