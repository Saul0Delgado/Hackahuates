"""
Voice Assistant Service with Gemini AI
========================================

Endpoint para asistente de voz que ayuda a operadores durante el armado de drawers.
Usa Gemini 1.5 Pro con contexto operacional completo para responder preguntas.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
import os

# Importar Gemini (necesita: pip install google-generativeai)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Voice assistant will use fallback responses.")

router = APIRouter(prefix="/api/v1/productivity", tags=["productivity"])

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    model = None

# ============================================================================
# MODELS
# ============================================================================

class DrawerContext(BaseModel):
    """Contexto del drawer actual que está armando el operador"""
    drawer_id: str = Field(..., description="ID único del drawer", example="DRW_001")
    flight_type: str = Field(..., description="Tipo de vuelo", example="Business")
    category: str = Field(..., description="Categoría del drawer", example="Beverage")
    total_items: int = Field(..., description="Total de items", example=12)
    unique_item_types: int = Field(..., description="Tipos únicos de items", example=4)
    item_list: str = Field(..., description="Lista de items separados por coma", example="CUTL01, CUP01, SNK01")
    airline: str = Field(default="Aeromexico", description="Aerolínea del vuelo")
    contract_id: str = Field(default="AM_STD_001", description="ID del contrato")

class VoiceQuery(BaseModel):
    """Query de voz del operador"""
    question: str = Field(..., description="Pregunta del operador", example="¿Dónde pongo el CUTL01?")
    drawer_context: Optional[DrawerContext] = Field(None, description="Contexto del drawer actual")

class VoiceResponse(BaseModel):
    """Respuesta del asistente de voz"""
    answer: str = Field(..., description="Respuesta en lenguaje natural")
    confidence: float = Field(..., description="Nivel de confianza 0-1")
    drawer_id: Optional[str] = Field(None, description="ID del drawer relacionado")
    suggestions: Optional[list] = Field(default=[], description="Sugerencias adicionales")

# ============================================================================
# KNOWLEDGE BASE
# ============================================================================

OPERATIONAL_KNOWLEDGE = """
OPERATIONAL KNOWLEDGE FOR GATEGROUP CATERING:
==============================================

1. DRAWER CONFIGURATION STANDARDS:
   Beverage Drawers:
   - Organize drinks by type (sodas, water, juice)
   - Heavy bottles at bottom for stability
   - Group by brand/flavor for quick identification

   Breakfast Drawers:
   - Bread, butter, jam, fruits, cutlery
   - Perishables checked for expiration
   - Bread products away from liquids

   Snack Drawers:
   - Chips, cookies, nuts, napkins
   - Fragile items (chips) on top
   - Small items in organized sections

   Meal Drawers:
   - Complete meal components + utensils
   - Temperature-sensitive items separate
   - Ensure all components present

   PLACEMENT RULES (CRITICAL):
   - Heavy items (DRK bottles, cans) → BOTTOM LAYER for stability
   - Fragile items (CUP cups, chips) → TOP LAYER, handle carefully
   - Frequently accessed (CUTL cutlery, NAP napkins) → EASY ACCESS positions
   - Group similar items together for visual organization
   - Never block access to items needed during service

2. ITEM CODES DICTIONARY:
   CUTL01/CUTL02: Cutlery sets (knives, forks, spoons, napkins)
   CUP01/CUP02: Cups and glasses (plastic/paper)
   SNK01-SNK05: Snacks (chips, cookies, crackers, nuts, pretzels)
   DRK01-DRK05: Drinks (Coca-Cola, Sprite, water, juice, coffee)
   BUT01/BUT02: Butter portions (salted, unsalted)
   JAM01/JAM02: Jam/preserves (strawberry, mixed fruit)
   BRD01/BRD02: Bread products (rolls, croissants)
   FRU01/FRU02: Fruit portions (fresh, dried)
   STR01: Stirrers for drinks
   SUG01: Sugar packets
   NAP01: Extra napkins
   TIS01: Tissues
   MIL01: Milk portions

3. PRODUCTIVITY & EFFICIENCY TIPS:
   - Target assembly time: ~4 hours for full flight (~7 carts)
   - Pre-stage high-frequency items saves 18-25% time:
     * CUTL01 appears in 45% of drawers
     * JAM02 appears in 44% of drawers
     * SUG01 appears in 43% of drawers

   Optimal Assembly Sequence:
   1. Preparation (30 sec): Verify drawer ID, check cleanliness
   2. Base layer (60-90 sec): Heavy items, stable foundation
   3. Middle layer (60-120 sec): Food items, grouped by type
   4. Top layer (30-60 sec): Light/fragile items, easy access
   5. Final check (15-30 sec): Count items, verify layout

   Speed Techniques:
   - Use BOTH HANDS simultaneously for symmetric placement
   - Follow consistent sequence to build muscle memory
   - Keep workspace organized (3 stations: liquids, snacks, misc)
   - Minimize unnecessary movements
   - Check manifest before starting to plan route

   Complexity Scoring:
   - Score = (Unique_Items / Total_Items) × 100
   - Low complexity (<30): 3-4 minutes
   - Medium (30-60): 5-6 minutes
   - High (>60): 7+ minutes

4. EXPIRATION & FIFO (FIRST IN, FIRST OUT):
   - Check expiration 5-7 days BEFORE expiry date
   - Items within 5 days of expiration → DISCARD
   - Always use oldest lots first (FIFO principle)
   - Each lot has uniform expiration date
   - Maximum 2-3 lots in rotation at once
   - Post-flight: recount and verify expiration dates

   Expiration Management:
   - Read lot numbers carefully (LOT-E19, LOT-A68, etc.)
   - Older lot letters (A, B) used before newer (E, F)
   - Check physical products if date unclear
   - Report expiration issues immediately

5. ASSEMBLY WORKFLOW:
   Step 1: PREPARATION (30 sec)
      □ Verify drawer ID matches manifest
      □ Inspect drawer is clean, sanitized
      □ Review complete item list
      □ Identify any special items/notes

   Step 2: BASE LAYER - Heavy Items (60-90 sec)
      □ Place all DRK (drinks, bottles, cans)
      □ Distribute weight evenly across drawer
      □ Ensure stable base, nothing wobbling
      □ Heavy items should NOT move when drawer shifts

   Step 3: MIDDLE LAYER - Food Items (60-120 sec)
      □ Add BRD (bread), BUT (butter), JAM (jam)
      □ Add SNK (snacks), FRU (fruit)
      □ Group by category for organization
      □ Check expiration dates as you place

   Step 4: TOP LAYER - Light/Fragile (30-60 sec)
      □ Add CUTL (cutlery), CUP (cups)
      □ Add NAP (napkins), TIS (tissues), STR (stirrers), SUG (sugar)
      □ Ensure easy access for crew during service
      □ Fragile items protected from pressure

   Step 5: FINAL CHECK (15-30 sec)
      □ Count total items vs. manifest (must match exactly)
      □ Verify no items blocking access paths
      □ Check weight distribution (drawer balanced)
      □ Verify contract-specific requirements met
      □ Sign off on completion

6. COMMON MISTAKES TO AVOID:
   ❌ Placing heavy items on top of fragile ones → Damage, waste
   ❌ Mixing drink types randomly → Slower crew identification
   ❌ Blocking cutlery access → Crew has to reorganize mid-service
   ❌ Forgetting expiration checks → Safety/compliance issues
   ❌ Not following FIFO → Products expire, waste
   ❌ Overpacking drawer → Items get crushed
   ❌ Undercounting items → Shortages on flight
   ❌ Ignoring manifest changes → Wrong configuration

7. QUALITY CHECKPOINTS:
   After base layer: Verify stability, no shifting
   After middle layer: Count snacks (high-error category)
   After top layer: Accessibility test (can reach all items easily)
   Final: Total count must equal manifest exactly

   Red Flags to Report:
   - Damaged products
   - Missing items that cannot be substituted
   - Expired products
   - Wrong item codes
   - Drawer physical damage
"""

CONTRACT_RULES = {
    "Aeromexico": """
AEROMEXICO CONTRACT RULES:
==========================
Verification time target: 10 seconds (down from 30 seconds manual)

Open/Partial Products:
✓ CAN reuse bottles if >50% full
✓ CAN combine bottles to meet volume (e.g., 2 halves = 1 liter)
✗ CANNOT reuse wine with cork (even if not consumed)
✗ CANNOT use bottles <50% full

Minimum Stock Requirements:
- 3× Coca-Cola regular
- 3× Coca-Cola Zero
- 2× Sprite
- (Adjust based on manifest)

Volume Requirements:
- Total volume must be met regardless of bottle combination
- Example: Need 2L juice → accept 1×1L + 2×0.5L bottles

Quality Standards:
- Products in good condition (no dents, tears)
- Labels readable
- Temperature appropriate for product type
""",

    "Delta": """
DELTA CONTRACT RULES:
=====================
Verification time target: 10 seconds

Open/Partial Products:
✗ CANNOT reuse ANY open bottles
✓ ONLY sealed bottles in original packaging accepted
✗ NO combining partial products

Quality Standards (STRICTER):
- Zero tolerance for damaged packaging
- All seals intact
- No substitutions without approval
- Premium presentation required

Stock Requirements:
- Per manifest exactly (no flexibility)
- Premium brands only in specific categories
""",

    "United": """
UNITED CONTRACT RULES:
======================
Verification time target: 10 seconds

Open/Partial Products:
✗ Bottles <50% must be discarded
✓ Bottles >50% can combine to meet volume
✓ Some flexibility on product substitutions

Quality Standards (MEDIUM):
- Standard packaging acceptable
- Minor cosmetic damage OK if product intact
- Reasonable substitutions allowed with notification

Stock Requirements:
- Per manifest with ±5% tolerance
- Standard brands accepted
"""
}

ITEM_METADATA = {
    "CUTL01": {"name": "Cutlery Set Standard", "weight": "50g", "fragile": False, "frequency": "45%"},
    "CUTL02": {"name": "Cutlery Set Premium", "weight": "75g", "fragile": False, "frequency": "30%"},
    "CUP01": {"name": "Plastic Cup 200ml", "weight": "15g", "fragile": True, "frequency": "35%"},
    "CUP02": {"name": "Paper Cup 300ml", "weight": "20g", "fragile": True, "frequency": "25%"},
    "SNK01": {"name": "Chips Pack", "weight": "25g", "fragile": True, "frequency": "38%"},
    "SNK02": {"name": "Cookies Pack", "weight": "30g", "fragile": False, "frequency": "40%"},
    "SNK03": {"name": "Crackers Pack", "weight": "20g", "fragile": True, "frequency": "28%"},
    "SNK04": {"name": "Nuts Pack", "weight": "35g", "fragile": False, "frequency": "41%"},
    "SNK05": {"name": "Pretzels Pack", "weight": "28g", "fragile": False, "frequency": "42%"},
    "DRK01": {"name": "Coca-Cola Can 355ml", "weight": "370g", "fragile": False, "frequency": "33%"},
    "DRK02": {"name": "Sprite Can 355ml", "weight": "370g", "fragile": False, "frequency": "30%"},
    "DRK03": {"name": "Water Bottle 500ml", "weight": "500g", "fragile": False, "frequency": "40%"},
    "DRK04": {"name": "Orange Juice 330ml", "weight": "350g", "fragile": False, "frequency": "25%"},
    "DRK05": {"name": "Coffee Instant Stick", "weight": "5g", "fragile": False, "frequency": "38%"},
    "BUT01": {"name": "Butter Salted 10g", "weight": "10g", "fragile": False, "frequency": "35%"},
    "BUT02": {"name": "Butter Unsalted 10g", "weight": "10g", "fragile": False, "frequency": "28%"},
    "JAM01": {"name": "Strawberry Jam 15g", "weight": "20g", "fragile": False, "frequency": "38%"},
    "JAM02": {"name": "Mixed Fruit Jam 15g", "weight": "20g", "fragile": False, "frequency": "44%"},
    "BRD01": {"name": "Bread Roll", "weight": "50g", "fragile": False, "frequency": "32%"},
    "BRD02": {"name": "Croissant", "weight": "60g", "fragile": False, "frequency": "30%"},
    "FRU01": {"name": "Fresh Fruit Cup", "weight": "120g", "fragile": False, "frequency": "39%"},
    "FRU02": {"name": "Dried Fruit Pack", "weight": "40g", "fragile": False, "frequency": "35%"},
    "STR01": {"name": "Drink Stirrer", "weight": "2g", "fragile": False, "frequency": "39%"},
    "SUG01": {"name": "Sugar Packet 5g", "weight": "5g", "fragile": False, "frequency": "43%"},
    "NAP01": {"name": "Napkin Pack", "weight": "10g", "fragile": False, "frequency": "37%"},
    "TIS01": {"name": "Tissue Pack", "weight": "15g", "fragile": False, "frequency": "32%"},
    "MIL01": {"name": "Milk Portion 20ml", "weight": "25g", "fragile": False, "frequency": "35%"},
}

# ============================================================================
# CONTEXT BUILDER
# ============================================================================

def build_system_context(drawer_context: DrawerContext) -> str:
    """
    Construye contexto completo del sistema para Gemini
    """

    # Obtener reglas del contrato
    contract_rules = CONTRACT_RULES.get(drawer_context.airline, CONTRACT_RULES["Aeromexico"])

    # Metadata de items en este drawer
    items = [x.strip() for x in drawer_context.item_list.split(',')]
    item_details = []
    for item_code in items[:20]:  # Limitar a 20 para no saturar contexto
        if item_code in ITEM_METADATA:
            meta = ITEM_METADATA[item_code]
            item_details.append(
                f"- {item_code}: {meta['name']} ({meta['weight']}, "
                f"{'Fragile' if meta['fragile'] else 'Sturdy'}, "
                f"Used in {meta['frequency']} of drawers)"
            )

    item_metadata_text = "\n".join(item_details) if item_details else "Standard items"

    # Calcular complexity score
    complexity_score = (drawer_context.unique_item_types / drawer_context.total_items) * 100
    if complexity_score < 30:
        complexity_level = "LOW (3-4 min estimated)"
    elif complexity_score < 60:
        complexity_level = "MEDIUM (5-6 min estimated)"
    else:
        complexity_level = "HIGH (7+ min estimated)"

    system_prompt = f"""You are an expert AI assistant for GateGroup airline catering operations.
You help workers assemble meal service drawers (trolleys) efficiently and correctly.
You provide CONCISE, ACTIONABLE answers that workers can understand while working hands-free.

CURRENT WORK CONTEXT:
====================
Drawer ID: {drawer_context.drawer_id}
Flight Type: {drawer_context.flight_type}
Category: {drawer_context.category}
Total Items: {drawer_context.total_items}
Unique Item Types: {drawer_context.unique_item_types}
Complexity Score: {complexity_score:.1f} ({complexity_level})
Item List: {drawer_context.item_list}
Airline: {drawer_context.airline}
Contract: {drawer_context.contract_id}

{OPERATIONAL_KNOWLEDGE}

{contract_rules}

ITEMS IN THIS DRAWER:
=====================
{item_metadata_text}

RESPONSE GUIDELINES (CRITICAL):
================================
1. Keep answers CONCISE: Maximum 2-3 sentences
2. Start with ACTION: "Place in...", "Yes, you can...", "No, discard..."
3. Use SPECIFIC terms: Item codes (CUTL01), positions (bottom left, top right)
4. Mention CONTRACT RULES when relevant
5. Provide brief REASONING (why)
6. For YES/NO questions: Start with YES or NO clearly
7. Use CONVERSATIONAL tone (the worker hears this spoken aloud)
8. NEVER use bullet points or formatting (this is spoken, not written)
9. Focus on IMMEDIATE ACTIONABLE guidance

Examples of good responses:
- "Place CUTL01 in the top layer, right side, for easy crew access. It's in 45 percent of drawers so keep it accessible."
- "Yes, for Aeromexico you can reuse that Sprite bottle if it's more than 50 percent full. Make sure total volume meets the 2 Sprite minimum."
- "No, discard it. The rule is 5 to 7 days before expiration. With only 4 days left it's outside safety margin."

Bad responses (avoid):
- Long explanations
- Bullet points or lists
- Technical jargon without context
- Vague guidance ("somewhere near the front")
- No clear action
"""

    return system_prompt

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/voice-assistant", response_model=VoiceResponse)
async def voice_assistant(query: VoiceQuery):
    """
    Endpoint principal para el asistente de voz activado por micrófono.

    El operador hace una pregunta por voz, el sistema:
    1. Recibe transcripción (speech-to-text en frontend)
    2. Construye contexto completo del drawer + conocimiento operacional
    3. Consulta Gemini 1.5 Pro
    4. Retorna respuesta concisa
    5. Frontend convierte a voz (text-to-speech)

    Examples:
        Query: "¿Dónde pongo el CUTL01?"
        Response: "Coloca CUTL01 en capa superior, lado derecho, para fácil acceso..."

        Query: "¿Puedo reusar esta botella de Sprite a la mitad?"
        Response: "Sí, para Aeromexico puedes reusar si está más del 50% llena..."
    """

    # Validar que haya contexto
    if not query.drawer_context:
        return VoiceResponse(
            answer="Por favor selecciona un drawer primero para poder ayudarte mejor con información específica.",
            confidence=1.0,
            suggestions=["Selecciona un drawer del menú", "Verifica que el drawer ID sea correcto"]
        )

    # Si Gemini no está disponible, usar fallback
    if not GEMINI_AVAILABLE or not model:
        return _fallback_response(query)

    try:
        # Construir contexto del sistema
        system_context = build_system_context(query.drawer_context)

        # Construir prompt completo
        full_prompt = f"""{system_context}

Worker question: {query.question}

Provide a helpful, concise answer (2-3 sentences max) that will be spoken aloud to the worker."""

        # Llamar a Gemini
        response = model.generate_content(full_prompt)
        answer = response.text.strip()

        # Limpiar respuesta (remover markdown, bullets, etc.)
        answer = _clean_response_for_speech(answer)

        return VoiceResponse(
            answer=answer,
            confidence=0.95,
            drawer_id=query.drawer_context.drawer_id,
            suggestions=[]
        )

    except Exception as e:
        print(f"Error in voice assistant: {str(e)}")
        import traceback
        traceback.print_exc()

        return VoiceResponse(
            answer="Lo siento, hubo un error procesando tu pregunta. Por favor intenta de nuevo o consulta con tu supervisor.",
            confidence=0.0,
            drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
            suggestions=["Intenta reformular la pregunta", "Verifica tu conexión"]
        )

def _clean_response_for_speech(text: str) -> str:
    """
    Limpia la respuesta para que suene natural cuando se habla
    Remueve markdown, bullets, etc.
    """
    import re

    # Remover markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remover bullets
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remover headers markdown
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Normalizar espacios
    text = re.sub(r'\n\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def _fallback_response(query: VoiceQuery) -> VoiceResponse:
    """
    Respuestas fallback cuando Gemini no está disponible
    """

    question_lower = query.question.lower()

    # Respuestas simples basadas en keywords
    if "donde" in question_lower or "pongo" in question_lower:
        if "cutl" in question_lower:
            return VoiceResponse(
                answer="Coloca los cubiertos en la capa superior para fácil acceso de la tripulación.",
                confidence=0.8,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None
            )
        elif "drk" in question_lower or "bebida" in question_lower:
            return VoiceResponse(
                answer="Coloca las bebidas en la capa inferior para estabilidad por su peso.",
                confidence=0.8,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None
            )

    elif "reusar" in question_lower or "reuso" in question_lower or "botella" in question_lower:
        airline = query.drawer_context.airline if query.drawer_context else "Aeromexico"
        if airline == "Delta":
            return VoiceResponse(
                answer="No, para Delta solo se aceptan botellas selladas en empaque original.",
                confidence=0.9,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None
            )
        else:
            return VoiceResponse(
                answer="Para Aeromexico, puedes reusar botellas si están más del 50 por ciento llenas y el volumen total se cumple.",
                confidence=0.9,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None
            )

    elif "rapido" in question_lower or "velocidad" in question_lower:
        return VoiceResponse(
            answer="Pre-organiza los items únicos antes de empezar y usa ambas manos para items simétricos.",
            confidence=0.7,
            drawer_id=query.drawer_context.drawer_id if query.drawer_context else None
        )

    # Default fallback
    return VoiceResponse(
        answer="No tengo suficiente información para responder esa pregunta. Por favor consulta el manual o pregunta a tu supervisor.",
        confidence=0.3,
        drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
        suggestions=["Reformula la pregunta", "Consulta el manual de procedimientos"]
    )

@router.get("/drawer/{drawer_id}")
async def get_drawer_info(drawer_id: str):
    """
    Obtiene información de un drawer específico del dataset de productividad
    """
    # En producción, esto consultaría una base de datos
    # Por ahora, retornamos datos de ejemplo basados en el dataset

    drawer_examples = {
        "DRW_001": {
            "drawer_id": "DRW_001",
            "flight_type": "Business",
            "category": "Beverage",
            "total_items": 12,
            "unique_item_types": 4,
            "item_list": "CUTL01, CUTL02, CUP01, SNK01",
            "airline": "Aeromexico",
            "contract_id": "AM_STD_001"
        },
        "DRW_006": {
            "drawer_id": "DRW_006",
            "flight_type": "Business",
            "category": "Snack",
            "total_items": 36,
            "unique_item_types": 14,
            "item_list": "BUT01, SNK02, DRK01, SNK01, CUTL02, BRD02, STR01, SNK05, BRD01, DRK05, CUP02, CUTL01, DRK03, SUG01",
            "airline": "Aeromexico",
            "contract_id": "AM_STD_001"
        }
    }

    if drawer_id not in drawer_examples:
        raise HTTPException(status_code=404, detail=f"Drawer {drawer_id} not found")

    return drawer_examples[drawer_id]
