import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('muestra el título del producto', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /help chair/i })).toBeInTheDocument()
  })
})
