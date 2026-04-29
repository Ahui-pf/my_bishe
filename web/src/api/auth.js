import http from './http'

export function apiLogin(payload) {
  return http.post('/auth/login', payload)
}

export function apiRegister(payload) {
  return http.post('/auth/register', payload)
}

export function apiProfile() {
  return http.get('/auth/profile')
}



