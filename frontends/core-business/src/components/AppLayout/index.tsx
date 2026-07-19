import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import { useStore } from '@/store'
import { onSpaceChanged, onSpacesInvalidated } from '@jonex/shell-sdk'

const AppLayout = () => {
  const { global } = useStore()
  useDocumentTitle()

  useEffect(() => {
    global.loadSpaces()

    const unsubChanged = onSpaceChanged((spaceId) => {
      global.setCurrentSpaceId(spaceId, { persist: false, broadcast: false })
    })
    const unsubInvalidated = onSpacesInvalidated(() => {
      global.refreshSpaces()
    })

    return () => {
      unsubChanged()
      unsubInvalidated()
    }
  }, [])

  return <Outlet />
}

export default AppLayout
