"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Camera, Upload, X, Package, Lightbulb, TrendingUp, AlertTriangle } from "lucide-react"

interface Product {
  id: string
  name: string
  category: string
  image?: string
}

const PRODUCTS: Product[] = [
  { id: "pan", name: "Pan", category: "Panadería" },
  { id: "chocolate", name: "Chocolate", category: "Snacks" },
  { id: "cafe", name: "Café", category: "Bebidas" },
  { id: "te", name: "Té", category: "Bebidas" },
  { id: "jugo", name: "Jugo", category: "Bebidas" },
  { id: "galletas", name: "Galletas", category: "Snacks" },
  { id: "fruta", name: "Fruta", category: "Alimentos Frescos" },
  { id: "yogurt", name: "Yogurt", category: "Lácteos" },
  { id: "sandwich", name: "Sandwich", category: "Alimentos" },
  { id: "ensalada", name: "Ensalada", category: "Alimentos Frescos" },
]

export function ProductsManager() {
  const [products, setProducts] = useState<Product[]>(PRODUCTS)
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({})

  const handleImageUpload = (productId: string, file: File) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      setProducts((prev) => prev.map((p) => (p.id === productId ? { ...p, image: reader.result as string } : p)))
    }
    reader.readAsDataURL(file)
  }

  const handleFileChange = (productId: string, event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleImageUpload(productId, file)
    }
  }

  const removeImage = (productId: string) => {
    setProducts((prev) => prev.map((p) => (p.id === productId ? { ...p, image: undefined } : p)))
  }

  const triggerFileInput = (productId: string) => {
    fileInputRefs.current[productId]?.click()
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

      {/* Products Grid */}
      <section aria-labelledby="products-section">
        <h3 id="products-section" className="text-lg font-semibold text-foreground mb-4">
          Catálogo de Productos
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.map((product) => (
            <Card key={product.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <CardTitle className="text-base">{product.name}</CardTitle>
                    <CardDescription className="text-xs mt-1">{product.category}</CardDescription>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {product.image ? "Con imagen" : "Sin imagen"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Image Preview */}
                <div
                  className="relative aspect-square rounded-lg bg-muted overflow-hidden border-2 border-dashed border-border"
                  role="img"
                  aria-label={product.image ? `Imagen de ${product.name}` : `Sin imagen para ${product.name}`}
                >
                  {product.image ? (
                    <>
                      <img
                        src={product.image || "/placeholder.svg"}
                        alt={product.name}
                        className="h-full w-full object-cover"
                      />
                      <Button
                        variant="destructive"
                        size="sm"
                        className="absolute top-2 right-2 h-8 w-8 p-0"
                        onClick={() => removeImage(product.id)}
                        aria-label={`Eliminar imagen de ${product.name}`}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <Package className="h-12 w-12 text-muted-foreground/30" aria-hidden="true" />
                    </div>
                  )}
                </div>

                {/* Upload Buttons */}
                <div className="flex gap-2">
                  <input
                    ref={(el) => { fileInputRefs.current[product.id] = el }}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleFileChange(product.id, e)}
                    aria-label={`Seleccionar archivo para ${product.name}`}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 gap-2 bg-transparent"
                    onClick={() => triggerFileInput(product.id)}
                    aria-label={`Subir imagen para ${product.name}`}
                  >
                    <Upload className="h-4 w-4" />
                    Subir
                  </Button>
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    id={`camera-${product.id}`}
                    onChange={(e) => handleFileChange(product.id, e)}
                    aria-label={`Tomar foto para ${product.name}`}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 gap-2 bg-transparent"
                    onClick={() => document.getElementById(`camera-${product.id}`)?.click()}
                    aria-label={`Tomar foto para ${product.name}`}
                  >
                    <Camera className="h-4 w-4" />
                    Cámara
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
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
    </div>
  )
}
