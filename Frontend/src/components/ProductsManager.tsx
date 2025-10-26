"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Select } from "./ui/select"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Camera, Upload, X, Package, Lightbulb, TrendingUp, AlertTriangle, Check, Calendar,Trash2 } from "lucide-react"
import { WebcamModal } from "./WebcamModal"

interface Product {
  id: string
  name: string
  image?: string
  expirationDate?: string
}

interface AssignedProduct {
  id: string; // ID único para la instancia
  productId: string;
  productName: string;
  image: string;
  expirationDate?: string;
}

const PRODUCTS: Product[] = [
  { id: "1", name: "Bebidas frías" },
  { id: "2", name: "Snacks Salados" },
  { id: "3", name: "Alcohol" },
  { id: "4", name: "Bebidas Calientes" },
  { id: "5", name: "Snacks Dulces" },
  { id: "6", name: "Comida Fresca" },
]

const API_URL = "http://localhost:5000/api"


export function ProductsManager() {
  const [products, setProducts] = useState<Product[]>(PRODUCTS)
  const [assignedProducts, setAssignedProducts] = useState<AssignedProduct[]>([])
  const [tempImage, setTempImage] = useState<string | null>(null)
  const [selectedProductId, setSelectedProductId] = useState<string>("")
  const [expirationDate, setExpirationDate] = useState<string>("")
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const cameraInputRef = useRef<HTMLInputElement | null>(null)
  const [isWebcamOpen, setIsWebcamOpen] = useState(false)
  const [isDetectingDate, setIsDetectingDate] = useState(false)
  const [detectionError, setDetectionError] = useState<string | null>(null)

  const handleTempImageUpload = (file: File) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      setTempImage(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleTempImageUpload(file)
      setDetectionError(null)
      setExpirationDate("") // Limpia la fecha anterior
      setIsDetectingDate(true)

      const formData = new FormData()
      formData.append('image', file)

      try {
        const response = await fetch(`${API_URL}/extraction/extract_date_from_image`, {
          method: "POST",
          body: formData,
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || "Error del servidor al detectar fecha")
        }

        const data = await response.json()

        if (data.success && data.date) {
          setExpirationDate(data.date) // ¡Establece la fecha encontrada!
        } else {
          throw new Error(data.error || "No se pudo encontrar una fecha en la imagen")
        }
      } catch (error) {
        console.error("Error al detectar fecha:", error)
        setDetectionError(error instanceof Error ? error.message : "Error desconocido")
      } finally {
        setIsDetectingDate(false)
      }
    }
  }

  const assignImageToProduct = () => {
    if (!tempImage || !selectedProductId) {
      alert("Por favor selecciona un producto y carga una imagen")
      return
    }

    // 1. Encontrar el nombre del producto seleccionado
    const selectedProduct = products.find(p => p.id === selectedProductId)
    if (!selectedProduct) {
      alert("Producto no encontrado")
      return
    }

    // 2. Crear el nuevo objeto de producto asignado
    const newAssignedProduct: AssignedProduct = {
      id: `prod-${Date.now()}`, // ID único para la fila de la tabla
      productId: selectedProductId,
      productName: selectedProduct.name,
      image: tempImage,
      expirationDate: expirationDate || undefined,
    }

    // 3. Añadir el nuevo producto a la lista de la tabla (al principio)
    setAssignedProducts(prev => [newAssignedProduct, ...prev])

    // 4. Resetear estados del formulario
    setTempImage(null)
    setSelectedProductId("")
    setExpirationDate("")
    setDetectionError(null)
  }

  // NUEVO: Función para eliminar un producto de la tabla
  const removeAssignedProduct = (idToRemove: string) => {
    setAssignedProducts(prev => prev.filter(p => p.id !== idToRemove))
  }

  const handleWebcamCapture = async (dataUrl: string) => {
    setTempImage(dataUrl)
    setIsWebcamOpen(false)

    setDetectionError(null)
    setExpirationDate("") 
    setIsDetectingDate(true)

    try {
      // 1. Quitar el prefijo 'data:image/jpeg;base64,'
      const base64Image = dataUrl.split('base64,')[1]

      const response = await fetch(`${API_URL}/extraction/extract_date`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          base_64_image_content: base64Image,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Error del servidor al detectar fecha")
      }

      const data = await response.json()

      if (data.success && data.date) {
        setExpirationDate(data.date) // ¡Establece la fecha encontrada!
      } else {
        throw new Error(data.error || "No se pudo encontrar una fecha en la imagen")
      }
    } catch (error) {
      console.error("Error al detectar fecha:", error)
      setDetectionError(error instanceof Error ? error.message : "Error desconocido")
    } finally {
      setIsDetectingDate(false)
    }
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

            {isDetectingDate && (
              <div className="flex items-center justify-center gap-2 text-primary pt-4">
                <Lightbulb className="h-4 w-4 animate-pulse" aria-hidden="true" />
                <p className="text-sm">Detectando fecha de caducidad...</p>
              </div>
            )}

            {detectionError && (
              <div className="flex items-center justify-center gap-2 text-destructive pt-4">
                <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                <p className="text-sm font-medium">{detectionError}</p>
              </div>
            )}

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
                  {isDetectingDate ? "Intentando detectar..." : "Ingresa manualmente si la detección falla"}
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
      
      {assignedProducts.length > 0 && (
        <section aria-labelledby="assigned-products-section">
          <div className="flex items-center gap-3 mb-4">
            <Package className="h-5 w-5 text-primary" aria-hidden="true" />
            <h3 id="assigned-products-section" className="text-lg font-semibold text-foreground">
              Productos Asignados
            </h3>
          </div>
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr className="border-b">
                      <th className="p-4 text-left font-medium text-muted-foreground">Producto</th>
                      <th className="p-4 text-left font-medium text-muted-foreground">Imagen</th>
                      <th className="p-4 text-left font-medium text-muted-foreground">Fecha de Caducidad</th>
                      <th className="p-4 text-left font-medium text-muted-foreground">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignedProducts.map((product) => (
                      <tr key={product.id} className="border-b last:border-b-0">
                        <td className="p-4 align-top font-medium">{product.productName}</td>
                        <td className="p-4 align-top">
                          <img
                            src={product.image}
                            alt={product.productName}
                            className="h-16 w-16 object-cover rounded-md border"
                          />
                        </td>
                        <td className="p-4 align-top">
                          {product.expirationDate ? (
                            <span>{product.expirationDate}</span>
                          ) : (
                            <span className="text-muted-foreground">N/A</span>
                          )}
                        </td>
                        <td className="p-4 align-top">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => removeAssignedProduct(product.id)}
                            aria-label="Eliminar producto"
                            className="gap-2"
                          >
                            <Trash2 className="h-4 w-4" />
                            Quitar
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </section>
      )}

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
