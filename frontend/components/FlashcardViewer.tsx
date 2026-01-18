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
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
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
            className="absolute inset-0 w-full h-full bg-gradient-to-br from-indigo-50 to-purple-50 rounded-3xl shadow-2xl border-2 border-indigo-100 flex flex-col items-center justify-center p-8"
            style={{
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden'
            }}
          >
            <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-4">
              Question
            </div>
            <h2 className="text-3xl font-bold text-gray-800 text-center mb-6">
              {currentCard.front}
            </h2>
            <div className="flex items-center gap-2 text-sm text-gray-500 mt-auto">
              <RotateCw size={16} />
              <span>Click to flip</span>
            </div>
          </div>

          {/* Back of card */}
          <div
            className="absolute inset-0 w-full h-full bg-gradient-to-br from-purple-50 to-indigo-50 rounded-3xl shadow-2xl border-2 border-purple-100 flex flex-col items-center justify-center p-8"
            style={{
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden',
              transform: 'rotateY(180deg)'
            }}
          >
            <div className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-4">
              Answer
            </div>
            <p className="text-lg text-gray-700 text-center leading-relaxed">
              {currentCard.back}
            </p>
            <div className="flex items-center gap-2 text-sm text-gray-500 mt-auto">
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
          className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-gray-200 rounded-xl font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
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
                  ? 'bg-indigo-500 w-8'
                  : idx < currentIndex
                  ? 'bg-indigo-300'
                  : 'bg-gray-300'
              }`}
              aria-label={`Go to card ${idx + 1}`}
            />
          ))}
        </div>

        <button
          onClick={handleNext}
          disabled={currentIndex === flashcards.length - 1}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-indigo-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
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
