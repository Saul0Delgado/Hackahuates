"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Select } from "./ui/select"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Camera, Upload, X, Package, Lightbulb, TrendingUp, AlertTriangle, Check, Calendar } from "lucide-react"
import { WebcamModal } from "./WebcamModal"

interface Product {
  id: string
  name: string
  image?: string
  expirationDate?: string
}

const PRODUCTS: Product[] = [
  { id: "1", name: "Bebidas frías" },
  { id: "2", name: "Snacks Salados" },
  { id: "3", name: "Alcohol" },
  { id: "4", name: "Bebidas Calientes" },
  { id: "5", name: "Snacks Dulces" },
  { id: "6", name: "Comida Fresca" },
]

export function ProductsManager() {
  const [products, setProducts] = useState<Product[]>(PRODUCTS)
  const [tempImage, setTempImage] = useState<string | null>(null)
  const [selectedProductId, setSelectedProductId] = useState<string>("")
  const [expirationDate, setExpirationDate] = useState<string>("")
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const cameraInputRef = useRef<HTMLInputElement | null>(null)
  const [isWebcamOpen, setIsWebcamOpen] = useState(false)

  const handleTempImageUpload = (file: File) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      setTempImage(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleTempImageUpload(file)
    }
  }

  const assignImageToProduct = () => {
    if (!tempImage || !selectedProductId) {
      alert("Por favor selecciona un producto y carga una imagen")
      return
    }

    setProducts((prev) =>
      prev.map((p) =>
        p.id === selectedProductId ? { ...p, image: tempImage, expirationDate: expirationDate || undefined } : p,
      ),
    )

    // Resetear estados
    setTempImage(null)
    setSelectedProductId("")
    setExpirationDate("")
  }

  /*const removeImage = (productId: string) => {
    setProducts((prev) =>
      prev.map((p) => (p.id === productId ? { ...p, image: undefined, expirationDate: undefined } : p)),
    )
  }*/

  const handleWebcamCapture = (dataUrl: string) => {
    setTempImage(dataUrl)
    setIsWebcamOpen(false)
  }

  const handleCameraClick = () => {
    // Detectar si es dispositivo móvil
    if (navigator.maxTouchPoints > 0) {
      // En móvil, usar el input nativo con capture
      cameraInputRef.current?.click()
    } else {
      // En desktop, abrir WebcamModal
      setIsWebcamOpen(true)
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
          <Package className="h-6 w-6 text-primary" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-foreground">Gestión de Productos</h2>
          <p className="text-sm text-muted-foreground">Administra imágenes y obtén recomendaciones</p>
        </div>
      </div>

      <section aria-labelledby="upload-section">
        <Card className="border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" aria-hidden="true" />
              Cargar Imagen de Producto
            </CardTitle>
            <CardDescription>Sube o toma una foto del producto y asígnala al producto correspondiente</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Vista previa de imagen temporal */}
            {tempImage && (
              <div className="relative aspect-video max-w-md mx-auto rounded-lg overflow-hidden border-2 border-primary/20">
                <img
                  src={tempImage || "/placeholder.svg"}
                  alt="Vista previa"
                  className="h-full w-full object-contain bg-muted"
                />
                <Button
                  variant="destructive"
                  size="sm"
                  className="absolute top-2 right-2 h-8 w-8 p-0"
                  onClick={() => setTempImage(null)}
                  aria-label="Eliminar imagen temporal"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Botones de carga */}
            <div className="flex gap-3 justify-center">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
                aria-label="Seleccionar archivo de imagen"
              />
              <Button
                variant="outline"
                className="gap-2 bg-transparent"
                onClick={() => fileInputRef.current?.click()}
                aria-label="Subir imagen desde archivo"
              >
                <Upload className="h-4 w-4" />
                Subir Archivo
              </Button>

              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={handleFileChange}
                aria-label="Tomar foto con cámara"
              />
              <Button
                variant="outline"
                className="gap-2 bg-transparent"
                onClick={handleCameraClick}
                aria-label="Tomar foto"
              >
                <Camera className="h-4 w-4" />
                Tomar Foto
              </Button>
            </div>

            {/* Formulario de asignación */}
            <div className="grid gap-4 max-w-md mx-auto pt-4 border-t">
              <div className="space-y-2">
                <Label htmlFor="product-select">Producto</Label>
                <Select
                  id="product-select"
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  aria-label="Seleccionar producto"
                >
                  <option value="">Selecciona un producto...</option>
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.name}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="expiration-date" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" aria-hidden="true" />
                  Fecha de Caducidad (Opcional)
                </Label>
                <Input
                  id="expiration-date"
                  type="date"
                  value={expirationDate}
                  onChange={(e) => setExpirationDate(e.target.value)}
                  aria-label="Fecha de caducidad del producto"
                />
                <p className="text-xs text-muted-foreground">
                  Ingresa manualmente si hay problemas con la detección automática
                </p>
              </div>

              <Button
                onClick={assignImageToProduct}
                disabled={!tempImage || !selectedProductId}
                className="gap-2"
                aria-label="Asignar imagen al producto"
              >
                <Check className="h-4 w-4" />
                Asignar Imagen
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Recommendations Section */}
      <section aria-labelledby="recommendations-section">
        <div className="flex items-center gap-3 mb-4">
          <Lightbulb className="h-5 w-5 text-primary" aria-hidden="true" />
          <h3 id="recommendations-section" className="text-lg font-semibold text-foreground">
            Recomendaciones de Productos
          </h3>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Recommendation Card 1 */}
          <Card className="border-l-4 border-l-primary">
            <CardHeader className="pb-3">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 flex-shrink-0">
                  <TrendingUp className="h-5 w-5 text-primary" aria-hidden="true" />
                </div>
                <div>
                  <CardTitle className="text-base">Productos de Alta Demanda</CardTitle>
                  <CardDescription className="text-xs mt-1">Basado en predicciones recientes</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-foreground/80" role="list">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
                  Café y Té tienen mayor demanda en vuelos matutinos
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
                  Snacks son preferidos en vuelos cortos
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
                  Comidas completas para vuelos largos
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Recommendation Card 2 */}
          <Card className="border-l-4 border-l-accent">
            <CardHeader className="pb-3">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 flex-shrink-0">
                  <Package className="h-5 w-5 text-accent" aria-hidden="true" />
                </div>
                <div>
                  <CardTitle className="text-base">Optimización de Inventario</CardTitle>
                  <CardDescription className="text-xs mt-1">Mejora la gestión de stock</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-foreground/80" role="list">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
                  Mantén stock extra de productos perecederos
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
                  Revisa fechas de caducidad semanalmente
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
                  Ajusta pedidos según temporada
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Recommendation Card 3 */}
          <Card className="border-l-4 border-l-destructive/50">
            <CardHeader className="pb-3">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-destructive/10 flex-shrink-0">
                  <AlertTriangle className="h-5 w-5 text-destructive" aria-hidden="true" />
                </div>
                <div>
                  <CardTitle className="text-base">Reducción de Desperdicio</CardTitle>
                  <CardDescription className="text-xs mt-1">Minimiza pérdidas</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-foreground/80" role="list">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-destructive/70" aria-hidden="true" />
                  Productos frescos tienen mayor desperdicio
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-destructive/70" aria-hidden="true" />
                  Usa predicciones para ajustar cantidades
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-destructive/70" aria-hidden="true" />
                  Monitorea patrones de consumo
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Webcam Modal */}
      <WebcamModal isOpen={isWebcamOpen} onClose={() => setIsWebcamOpen(false)} onPhotoTaken={handleWebcamCapture} />
    </div>
  )
}
