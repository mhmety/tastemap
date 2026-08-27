import { ChevronLeft, ChevronRight, Image } from 'lucide-react'
import type { JSX } from 'react'
import { useEffect, useMemo, useRef, useState } from 'react'

interface RestaurantPhotoCarouselProps {
  name: string
  thumbnail: string | null
  photos?: string[] | null
}

function clampIndex(index: number, length: number): number {
  if (length <= 0) return 0
  return ((index % length) + length) % length
}

export function RestaurantPhotoCarousel({
  name,
  thumbnail,
  photos,
}: RestaurantPhotoCarouselProps): JSX.Element {
  const [imageFailed, setImageFailed] = useState<Record<number, boolean>>({})
  const [activeIndex, setActiveIndex] = useState<number>(0)
  const [isHovered, setIsHovered] = useState<boolean>(false)
  const [touchStartX, setTouchStartX] = useState<number | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const imageUrls = useMemo(() => {
    const list = Array.isArray(photos) ? photos.filter((url) => typeof url === 'string' && url.trim()) : []
    if (list.length > 0) return list
    return thumbnail ? [thumbnail] : []
  }, [photos, thumbnail])

  const hasMultiplePhotos = imageUrls.length > 1

  const goToIndex = (nextIndex: number): void => {
    setActiveIndex((current) => clampIndex(nextIndex ?? current, imageUrls.length))
  }

  const handlePrevious = (): void => {
    setActiveIndex((current) => clampIndex(current - 1, imageUrls.length))
  }

  const handleNext = (): void => {
    setActiveIndex((current) => clampIndex(current + 1, imageUrls.length))
  }

  useEffect(() => {
    if (!hasMultiplePhotos) return
    if (isHovered) return

    const timer = window.setInterval(() => {
      setActiveIndex((current) => clampIndex(current + 1, imageUrls.length))
    }, 4500)

    return () => window.clearInterval(timer)
  }, [hasMultiplePhotos, imageUrls.length, isHovered])

  useEffect(() => {
    if (!hasMultiplePhotos) return
    if (!containerRef.current) return

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'ArrowLeft') {
        event.preventDefault()
        setActiveIndex((current) => clampIndex(current - 1, imageUrls.length))
      }
      if (event.key === 'ArrowRight') {
        event.preventDefault()
        setActiveIndex((current) => clampIndex(current + 1, imageUrls.length))
      }
    }

    const node = containerRef.current
    node.addEventListener('keydown', handleKeyDown)
    return () => node.removeEventListener('keydown', handleKeyDown)
  }, [hasMultiplePhotos, imageUrls.length])

  if (imageUrls.length === 0) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-2xl bg-gradient-to-br from-slate-50 to-slate-100 text-slate-400 sm:h-72 lg:h-full">
        <Image size={34} />
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      tabIndex={hasMultiplePhotos ? 0 : -1}
      className="relative h-64 w-full overflow-hidden rounded-2xl bg-slate-50 outline-none focus:ring-2 focus:ring-orange-200 sm:h-72 lg:h-full"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onTouchStart={(event) => setTouchStartX(event.touches[0]?.clientX ?? null)}
      onTouchEnd={(event) => {
        if (touchStartX == null) return
        const endX = event.changedTouches[0]?.clientX ?? touchStartX
        const delta = endX - touchStartX
        setTouchStartX(null)
        if (Math.abs(delta) < 40) return
        if (delta > 0) {
          setActiveIndex((current) => clampIndex(current - 1, imageUrls.length))
        } else {
          setActiveIndex((current) => clampIndex(current + 1, imageUrls.length))
        }
      }}
    >
      {imageUrls.map((url, index) => {
        const isActive = index === clampIndex(activeIndex, imageUrls.length)
        return (
          <div
            key={`${url}-${index}`}
            className={`absolute inset-0 transition-opacity duration-300 ease-in-out ${isActive ? 'opacity-100' : 'opacity-0'
              }`}
          >
            {imageFailed[index] ? (
              <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 text-slate-400">
                <Image size={34} />
              </div>
            ) : (
              <img
                src={url}
                alt={name}
                loading="lazy"
                referrerPolicy="no-referrer"
                className="h-full w-full object-cover"
                onError={() => setImageFailed((current) => ({ ...current, [index]: true }))}
              />
            )}
          </div>
        )
      })}

      {hasMultiplePhotos ? (
        <>
          <div className="absolute right-3 top-3 rounded-full bg-black/50 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
            {clampIndex(activeIndex, imageUrls.length) + 1} / {imageUrls.length}
          </div>
          <button
            type="button"
            aria-label="Önceki fotoğraf"
            className="absolute left-3 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 text-slate-700 shadow-sm backdrop-blur transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-orange-200 cursor-pointer"
            onClick={handlePrevious}
          >
            <ChevronLeft size={18} />
          </button>
          <button
            type="button"
            aria-label="Sonraki fotoğraf"
            className="absolute right-3 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 text-slate-700 shadow-sm backdrop-blur transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-orange-200 cursor-pointer"
            onClick={handleNext}
          >
            <ChevronRight size={18} />
          </button>

          <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full bg-white/70 px-3 py-2 backdrop-blur">
            {imageUrls.map((_, index) => (
              <button
                key={`photo-dot-${index}`}
                type="button"
                aria-label={`Fotoğraf ${index + 1}`}
                className={`h-2.5 w-2.5 rounded-full transition ${index === activeIndex ? 'bg-orange-500' : 'bg-slate-300 hover:bg-slate-400'
                  }`}
                onClick={() => goToIndex(index)}
              />
            ))}
          </div>
        </>
      ) : null}
    </div>
  )
}
