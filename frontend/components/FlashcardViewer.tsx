import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight, RotateCw } from 'lucide-react'

interface Flashcard {
  front: string
  back: string
}

interface FlashcardViewerProps {
  flashcards: Flashcard[]
}

export default function FlashcardViewer({ flashcards }: FlashcardViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        handlePrevious()
      } else if (e.key === 'ArrowRight') {
        handleNext()
      } else if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault()
        handleFlip()
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [currentIndex, isFlipped])

  if (!flashcards || flashcards.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No flashcards available
      </div>
    )
  }

  const currentCard = flashcards[currentIndex]

  const handleNext = () => {
    if (currentIndex < flashcards.length - 1) {
      setIsFlipped(false)
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setIsFlipped(false)
      setCurrentIndex(currentIndex - 1)
    }
  }

  const handleFlip = () => {
    setIsFlipped(!isFlipped)
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-semibold text-gray-600">
            Card {currentIndex + 1} of {flashcards.length}
          </span>
          <span className="text-xs text-gray-500">
            {Math.round(((currentIndex + 1) / flashcards.length) * 100)}% Complete
          </span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-teal-500 to-cyan-500"
            initial={{ width: 0 }}
            animate={{ width: `${((currentIndex + 1) / flashcards.length) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Flashcard */}
      <div className="relative perspective-1000 mb-8">
        <motion.div
          className="relative w-full h-[400px] cursor-pointer"
          onClick={handleFlip}
          style={{ transformStyle: 'preserve-3d' }}
          animate={{ rotateY: isFlipped ? 180 : 0 }}
          transition={{ duration: 0.6, type: 'spring', stiffness: 100 }}
        >
          {/* Front of card */}
          <div
            className="absolute inset-0 w-full h-full bg-gradient-to-br from-teal-50 via-cyan-50 to-blue-50 rounded-3xl shadow-2xl border-2 border-teal-200 flex flex-col items-center justify-center p-12"
            style={{
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden'
            }}
          >
            <div className="flex-1 flex items-center justify-center w-full">
              <h2 className="text-2xl md:text-3xl font-bold text-gray-800 text-center leading-relaxed">
                {currentCard.front}
              </h2>
            </div>
            <div className="flex items-center gap-2 text-sm text-teal-600 font-medium">
              <RotateCw size={16} />
              <span>Click to reveal</span>
            </div>
          </div>

          {/* Back of card */}
          <div
            className="absolute inset-0 w-full h-full bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 rounded-3xl shadow-2xl border-2 border-emerald-200 flex flex-col items-center justify-center p-12 relative overflow-hidden"
            style={{
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden',
              transform: 'rotateY(180deg)'
            }}
          >
            {/* Medical cross pattern in background */}
            <div className="absolute inset-0 opacity-5">
              <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                <pattern id="medical-cross" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M8 6h4v3h3v4h-3v3H8v-3H5V9h3V6z" fill="currentColor" className="text-teal-600" />
                </pattern>
                <rect width="100" height="100" fill="url(#medical-cross)" />
              </svg>
            </div>
            
            {/* Decorative corner accent */}
            <div className="absolute top-4 right-4 w-12 h-12 border-t-2 border-r-2 border-emerald-300 rounded-tr-2xl opacity-30"></div>
            <div className="absolute bottom-4 left-4 w-12 h-12 border-b-2 border-l-2 border-emerald-300 rounded-bl-2xl opacity-30"></div>
            
            {/* Medical icon */}
            <div className="absolute top-6 left-6 text-emerald-300 opacity-40">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M2 12h20M8 8l8 8M16 8l-8 8" />
              </svg>
            </div>
            
            <div className="flex-1 flex items-center justify-center w-full overflow-y-auto relative z-10">
              <div className="max-w-2xl">
                <p className="text-base md:text-lg text-gray-700 text-center leading-relaxed">
                  {currentCard.back}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 text-sm text-emerald-600 font-medium relative z-10">
              <RotateCw size={16} />
              <span>Click to flip back</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-gray-200 rounded-xl font-semibold text-gray-700 hover:bg-gray-50 hover:border-teal-300 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          <ChevronLeft size={20} />
          Previous
        </button>

        <div className="flex gap-2">
          {flashcards.map((_, idx) => (
            <button
              key={idx}
              onClick={() => {
                setCurrentIndex(idx)
                setIsFlipped(false)
              }}
              className={`w-2 h-2 rounded-full transition-all ${
                idx === currentIndex
                  ? 'bg-teal-500 w-8'
                  : idx < currentIndex
                  ? 'bg-teal-300'
                  : 'bg-gray-300'
              }`}
              aria-label={`Go to card ${idx + 1}`}
            />
          ))}
        </div>

        <button
          onClick={handleNext}
          disabled={currentIndex === flashcards.length - 1}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-teal-500 to-cyan-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-teal-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Next
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Keyboard Shortcuts Hint */}
      <div className="mt-6 text-center text-xs text-gray-400">
        <span className="inline-flex items-center gap-4">
          <span>← Previous</span>
          <span>Space to flip</span>
          <span>→ Next</span>
        </span>
      </div>

      <style jsx global>{`
        .perspective-1000 {
          perspective: 1000px;
        }
      `}</style>
    </div>
  )
}
