const TOKEN_KEY = 'token'

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
  return atob(padded)
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function parseTokenPayload(token) {
  if (!token) return null

  try {
    const [, payload] = token.split('.')
    if (!payload) return null
    return JSON.parse(decodeBase64Url(payload))
  } catch {
    return null
  }
}

export function isTokenExpired(token) {
  const payload = parseTokenPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 <= Date.now()
}

export function hasValidToken() {
  const token = getStoredToken()
  return Boolean(token) && !isTokenExpired(token)
}
