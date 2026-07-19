import { useState, useEffect } from 'react'

const checkIsMobile = (): boolean => {
  return (
    window.innerWidth <= 768 ||
    /Android|webOS|iPhone|iPod|BlackBerry|iPad|HarmonyOS|Mobile/i.test(
      navigator.userAgent
    )
  )
}

export default function useIsMobile(onChange?: (mobile: boolean) => void): boolean {
  const [isMobile, setIsMobile] = useState(checkIsMobile())

  useEffect(() => {
    const handleResize = () => {
      const mobile = checkIsMobile()
      setIsMobile(mobile)
      if (onChange) onChange(mobile)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [onChange])

  return isMobile
}
