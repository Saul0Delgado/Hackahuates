// En /components/WebcamModal.tsx
"use client"

import { useRef, useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./ui/dialog"
import { Button } from "./ui/button"
import { Camera, RefreshCcw } from "lucide-react"

interface WebcamModalProps {
  isOpen: boolean
  onClose: () => void
  onPhotoTaken: (dataUrl: string) => void
}

export function WebcamModal({ isOpen, onClose, onPhotoTaken }: WebcamModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 1. Función para iniciar la cámara
  const startCamera = async () => {
    // Limpia cualquier stream anterior
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
    }

    try {
      const newStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }, // Prioriza la externa/trasera
      })
      if (videoRef.current) {
        videoRef.current.srcObject = newStream
      }
      setStream(newStream)
      setError(null)
    } catch (err) {
      console.error("Error al acceder a la cámara:", err)
      setError("No se pudo acceder a la cámara. Revisa los permisos.")
      // Intenta con la cámara frontal si falla
      try {
        const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true })
        if (videoRef.current) {
          videoRef.current.srcObject = fallbackStream
        }
        setStream(fallbackStream)
        setError(null)
      } catch (fallbackErr) {
        console.error("Error al acceder a la cámara (fallback):", fallbackErr)
        setError("No se pudo acceder a ninguna cámara. Revisa los permisos.")
      }
    }
  }

  // 2. Función para detener la cámara
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      setStream(null)
    }
  }

  // 3. Inicia o detiene la cámara cuando el modal se abre/cierra
  useEffect(() => {
    if (isOpen) {
      startCamera()
    } else {
      stopCamera()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  // 4. Función para tomar la foto
  const handleTakePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current

    // Configura el tamaño del canvas al del video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Dibuja el frame actual del video en el canvas
    const context = canvas.getContext("2d")
    context?.drawImage(video, 0, 0, video.videoWidth, video.videoHeight)

    // Convierte el canvas a una imagen dataURL (Base64)
    const dataUrl = canvas.toDataURL("image/jpeg")

    // Envía la imagen al componente padre
    onPhotoTaken(dataUrl)
    onClose() // Cierra el modal
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[600px] p-0" onInteractOutside={(e) => e.preventDefault()}>
        <DialogHeader className="p-6 pb-2">
          <DialogTitle>Tomar Foto</DialogTitle>
        </DialogHeader>

        <div className="relative aspect-video bg-black">
          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-destructive p-4">
              <Camera className="h-12 w-12" />
              <p className="mt-2">{error}</p>
            </div>
          )}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className={`h-full w-full object-contain ${error ? "hidden" : ""}`}
          />
          {/* Canvas invisible para procesar la imagen */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        <DialogFooter className="p-6 pt-2 gap-2 sm:justify-between">
          <Button variant="outline" onClick={startCamera}>
            <RefreshCcw className="h-4 w-4 mr-2" />
            Reiniciar Cámara
          </Button>
          <Button onClick={handleTakePhoto} disabled={!!error || !stream}>
            <Camera className="h-4 w-4 mr-2" />
            Capturar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}