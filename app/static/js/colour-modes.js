/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2023 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

const getStoredTheme = () => localStorage.getItem('theme')
const setStoredTheme = theme => localStorage.setItem('theme', theme)

const getPreferredTheme = () => {
  const storedTheme = getStoredTheme()
  if (storedTheme) {
    return storedTheme
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const setTheme = theme => {
  document.documentElement.setAttribute('data-bs-theme', theme)
}

const toggleTheme = () => {
  const preferredTheme = getPreferredTheme()
  const nextTheme = preferredTheme === 'dark' ? 'light' : 'dark'
  setStoredTheme(nextTheme)
  setTheme(nextTheme)
}

setTheme(getPreferredTheme())
