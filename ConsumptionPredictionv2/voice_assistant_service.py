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
import base64
import requests

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)
    print(f"[INIT] ✓ Loaded .env file from: {dotenv_path}")
except ImportError:
    print("[INIT] ⚠ python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"[INIT] ⚠ Could not load .env file: {str(e)}")

# Importar Gemini (necesita: pip install google-generativeai)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("[INIT] ✓ Gemini library imported successfully")
except ImportError:
    GEMINI_AVAILABLE = False
    print("[INIT] ✗ Gemini library NOT available - will use fallback responses")

router = APIRouter(prefix="/api/v1/productivity", tags=["productivity"])

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("[INIT] ✗ GEMINI_API_KEY not found in environment variables or .env file")
    print("[INIT] ⚠ Make sure you have GEMINI_API_KEY in your .env file or system environment")
else:
    print(f"[INIT] ✓ GEMINI_API_KEY loaded successfully (length: {len(GEMINI_API_KEY)} chars)")
    print(f"[INIT] ✓ API Key starts with: {GEMINI_API_KEY[:10]}...")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        # Intentar usar gemini-2.0-flash primero (más nuevo)
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            print("[INIT] ✓ Gemini model initialized successfully (gemini-2.0-flash)")
        except Exception as e1:
            print(f"[INIT] ⚠ gemini-2.0-flash not available: {str(e1)}")
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                print("[INIT] ✓ Gemini model initialized successfully (gemini-1.5-flash)")
            except Exception as e2:
                print(f"[INIT] ⚠ gemini-1.5-flash not available: {str(e2)}")
                model = genai.GenerativeModel('gemini-pro')
                print("[INIT] ✓ Gemini model initialized successfully (gemini-pro)")

        print("[INIT] ✓✓✓ VOICE ASSISTANT READY - All systems operational ✓✓✓")
    except Exception as e:
        print(f"[INIT] ✗ Failed to initialize Gemini model: {str(e)}")
        model = None
else:
    model = None
    if not GEMINI_AVAILABLE:
        print(f"[INIT] ✗ Gemini model NOT initialized - Reason: Gemini library not available")
    elif not GEMINI_API_KEY:
        print(f"[INIT] ✗ Gemini model NOT initialized - Reason: GEMINI_API_KEY not set")
    else:
        print(f"[INIT] ✗ Gemini model NOT initialized - Reason: Unknown")

# Configurar ElevenLabs API
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY", "")
ELEVENLABS_VOICE_ID = "Xb7hH8MSUJpSbSDYk0k2"  # Paula - voz femenina en español natural
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

if not ELEVEN_LABS_API_KEY:
    print("[INIT] ✗ ELEVEN_LABS_API_KEY not found in environment variables or .env file")
    print("[INIT] ⚠ ElevenLabs TTS will not be available - frontend will use Web Speech API fallback")
    ELEVENLABS_AVAILABLE = False
else:
    print(f"[INIT] ✓ ELEVEN_LABS_API_KEY loaded successfully (length: {len(ELEVEN_LABS_API_KEY)} chars)")
    print(f"[INIT] ✓ Using ElevenLabs voice: {ELEVENLABS_VOICE_ID} (Paula - Spanish)")
    ELEVENLABS_AVAILABLE = True

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
    audio_base64: Optional[str] = Field(None, description="Audio de la respuesta en base64 (ElevenLabs TTS)")

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
                f"{'Frágil' if meta['fragile'] else 'Resistente'}, "
                f"Usado en {meta['frequency']} de gavetas)"
            )

    item_metadata_text = "\n".join(item_details) if item_details else "Items estándar"

    # Calcular complexity score
    complexity_score = (drawer_context.unique_item_types / drawer_context.total_items) * 100
    if complexity_score < 30:
        complexity_level = "BAJA (3-4 min estimados)"
    elif complexity_score < 60:
        complexity_level = "MEDIA (5-6 min estimados)"
    else:
        complexity_level = "ALTA (7+ min estimados)"

    system_prompt = f"""Eres un asistente de IA experto en operaciones de catering aéreo de GateGroup.
Ayudas a los operarios a armar gavetas de servicio de comidas (carritos) de manera eficiente y correcta.
Proporcionas respuestas CONCISAS y ACCIONABLES que los operarios puedan entender trabajando con las manos libres.
RESPONDE SIEMPRE EN ESPAÑOL. No mezcles inglés en tus respuestas.

CONTEXTO ACTUAL DE TRABAJO:
===========================
ID Gaveta: {drawer_context.drawer_id}
Tipo Vuelo: {drawer_context.flight_type}
Categoría: {drawer_context.category}
Total Items: {drawer_context.total_items}
Tipos Únicos: {drawer_context.unique_item_types}
Nivel Complejidad: {complexity_score:.1f} ({complexity_level})
Lista Items: {drawer_context.item_list}
Aerolínea: {drawer_context.airline}
Contrato: {drawer_context.contract_id}

{OPERATIONAL_KNOWLEDGE}

{contract_rules}

ITEMS EN ESTA GAVETA:
====================
{item_metadata_text}

GUÍAS DE RESPUESTA (CRÍTICAS):
==============================
1. Respuestas CONCISAS: Máximo 2-3 oraciones
2. Comienza con ACCIÓN: "Coloca en...", "Sí, puedes...", "No, descarta..."
3. Usa términos ESPECÍFICOS: Códigos de item (CUTL01), posiciones (abajo izquierda, arriba derecha)
4. Menciona REGLAS DE CONTRATO cuando sea relevante
5. Proporciona RAZONAMIENTO breve (por qué)
6. Para preguntas SÍ/NO: Comienza con SÍ o NO claramente
7. Usa tono CONVERSACIONAL (el operario escucha esto en voz alta)
8. NUNCA uses viñetas o formato especial (esto es hablado, no escrito)
9. Enfócate en orientación ACCIONABLE INMEDIATA
10. TODO EN ESPAÑOL - Sin excepciones

Ejemplos de buenas respuestas:
- "Coloca CUTL01 en la capa superior, lado derecho, para acceso fácil de la tripulación. Está en 45 por ciento de gavetas así que mantenlo accesible."
- "Sí, para Aeromexico puedes reusar esa botella de Sprite si está más del 50 por ciento llena. Asegúrate que el volumen total cumple el mínimo de 2 Sprites."
- "No, descártala. La regla es 5 a 7 días antes de vencer. Con solo 4 días quedan fuera del margen de seguridad."

Respuestas malas (evita):
- Explicaciones largas
- Viñetas o listas
- Jerga técnica sin contexto
- Orientación vaga ("en algún lugar al frente")
- Sin acción clara
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

    # Log: Nueva query recibida
    print(f"\n{'='*70}")
    print(f"[VOICE ASSISTANT] New query received")
    print(f"  Question: {query.question}")
    print(f"  Drawer ID: {query.drawer_context.drawer_id if query.drawer_context else 'None'}")
    print(f"  GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
    print(f"  Model initialized: {model is not None}")
    print(f"{'='*70}")

    # Validar que haya contexto
    if not query.drawer_context:
        print("[VOICE ASSISTANT] No drawer context provided")
        return VoiceResponse(
            answer="Por favor selecciona un drawer primero para poder ayudarte mejor con información específica.",
            confidence=1.0,
            suggestions=["Selecciona un drawer del menú", "Verifica que el drawer ID sea correcto"],
            audio_base64=None
        )

    # Si Gemini no está disponible, usar fallback
    if not GEMINI_AVAILABLE or not model:
        reason = "Gemini library not available" if not GEMINI_AVAILABLE else "Model not initialized"
        print(f"[FALLBACK TRIGGERED] Reason: {reason}")
        return _fallback_response(query)

    try:
        # Construir contexto del sistema
        system_context = build_system_context(query.drawer_context)

        # Construir prompt completo
        full_prompt = f"""{system_context}

Pregunta del operador: {query.question}

IMPORTANTE: Responde SIEMPRE en español. Tu respuesta debe ser:
- Concisa (máximo 2-3 oraciones)
- Directa y clara
- Natural para ser leída en voz alta
- 100% en español, sin mezclar inglés

Respuesta:"""

        # Log: Antes de llamar a Gemini
        print(f"[GEMINI CALL] Calling Gemini API...")
        print(f"[GEMINI CALL] Prompt length: {len(full_prompt)} characters")
        print(f"[GEMINI CALL] Question: {query.question}")

        # Llamar a Gemini
        response = model.generate_content(full_prompt)
        answer = response.text.strip()

        # Log: Respuesta recibida
        print(f"[GEMINI SUCCESS] Response received successfully")
        print(f"[GEMINI SUCCESS] Raw answer length: {len(answer)} characters")
        print(f"[GEMINI SUCCESS] Raw answer: {answer[:150]}..." if len(answer) > 150 else f"[GEMINI SUCCESS] Raw answer: {answer}")

        # Limpiar respuesta (remover markdown, bullets, etc.)
        answer = _clean_response_for_speech(answer)

        # Log: Respuesta limpia
        print(f"[GEMINI SUCCESS] Cleaned answer: {answer[:150]}..." if len(answer) > 150 else f"[GEMINI SUCCESS] Cleaned answer: {answer}")
        print(f"{'='*70}\n")

        # Generar audio con ElevenLabs
        audio_base64 = None
        if ELEVENLABS_AVAILABLE and ELEVEN_LABS_API_KEY:
            print(f"[VOICE ASSISTANT] Generating audio with ElevenLabs...")
            audio_base64 = await convert_text_to_speech_elevenlabs(answer)
            if audio_base64:
                print(f"[VOICE ASSISTANT] Audio generated successfully and encoded to base64")
            else:
                print(f"[VOICE ASSISTANT] Audio generation failed - frontend will use Web Speech API fallback")
        else:
            print(f"[VOICE ASSISTANT] ElevenLabs not available - frontend will use Web Speech API fallback")

        return VoiceResponse(
            answer=answer,
            confidence=0.95,
            drawer_id=query.drawer_context.drawer_id,
            suggestions=[],
            audio_base64=audio_base64
        )

    except Exception as e:
        print(f"[ERROR] Exception occurred in voice assistant")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback:")
        traceback.print_exc()
        print(f"{'='*70}\n")

        return VoiceResponse(
            answer="Lo siento, hubo un error procesando tu pregunta. Por favor intenta de nuevo o consulta con tu supervisor.",
            confidence=0.0,
            drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
            suggestions=["Intenta reformular la pregunta", "Verifica tu conexión"],
            audio_base64=None
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

async def convert_text_to_speech_elevenlabs(text: str) -> Optional[str]:
    """
    Convierte texto a voz usando ElevenLabs API
    Retorna: audio en base64 o None si falla

    Args:
        text: Texto a convertir a voz

    Returns:
        Base64 encoded audio string, or None if conversion fails
    """

    if not ELEVENLABS_AVAILABLE or not ELEVEN_LABS_API_KEY:
        print("[ELEVENLABS] Skipping TTS - ElevenLabs not available")
        return None

    if not text or len(text.strip()) == 0:
        print("[ELEVENLABS] Warning: Empty text provided for TTS")
        return None

    try:
        # Log: Antes de llamar a ElevenLabs
        print(f"[ELEVENLABS CALL] Converting text to speech...")
        print(f"[ELEVENLABS CALL] Text length: {len(text)} characters")
        print(f"[ELEVENLABS CALL] Voice ID: {ELEVENLABS_VOICE_ID}")
        print(f"[ELEVENLABS CALL] Model: {ELEVENLABS_MODEL_ID}")

        # Construir request a ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_LABS_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
            "language_code": "es",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": False
            }
        }

        # Hacer request
        print(f"[ELEVENLABS CALL] Sending request to ElevenLabs API...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        # Validar respuesta
        if response.status_code != 200:
            print(f"[ELEVENLABS ERROR] API returned status code {response.status_code}")
            print(f"[ELEVENLABS ERROR] Response: {response.text[:200]}")
            return None

        # Convertir audio a base64
        audio_bytes = response.content
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Log: Éxito
        print(f"[ELEVENLABS SUCCESS] Audio generated successfully")
        print(f"[ELEVENLABS SUCCESS] Audio size: {len(audio_bytes)} bytes")
        print(f"[ELEVENLABS SUCCESS] Base64 encoded, ready to send to frontend")

        return audio_base64

    except requests.Timeout:
        print(f"[ELEVENLABS ERROR] Request timeout after 30 seconds")
        return None
    except requests.RequestException as e:
        print(f"[ELEVENLABS ERROR] Request error: {str(e)}")
        return None
    except Exception as e:
        print(f"[ELEVENLABS ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ELEVENLABS ERROR] Error message: {str(e)}")
        return None

def _fallback_response(query: VoiceQuery) -> VoiceResponse:
    """
    Respuestas fallback cuando Gemini no está disponible
    """

    print(f"[FALLBACK RESPONSE] Processing fallback for: {query.question}")
    question_lower = query.question.lower()

    # Respuestas simples basadas en keywords
    if "donde" in question_lower or "pongo" in question_lower:
        print(f"[FALLBACK KEYWORD MATCH] 'donde/pongo' matched")
        if "cutl" in question_lower:
            return VoiceResponse(
                answer="Coloca los cubiertos en la capa superior para fácil acceso de la tripulación.",
                confidence=0.8,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
                audio_base64=None
            )
        elif "drk" in question_lower or "bebida" in question_lower:
            return VoiceResponse(
                answer="Coloca las bebidas en la capa inferior para estabilidad por su peso.",
                confidence=0.8,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
                audio_base64=None
            )

    elif "reusar" in question_lower or "reuso" in question_lower or "botella" in question_lower:
        print(f"[FALLBACK KEYWORD MATCH] 'reusar/reuso/botella' matched")
        airline = query.drawer_context.airline if query.drawer_context else "Aeromexico"
        if airline == "Delta":
            return VoiceResponse(
                answer="No, para Delta solo se aceptan botellas selladas en empaque original.",
                confidence=0.9,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
                audio_base64=None
            )
        else:
            return VoiceResponse(
                answer="Para Aeromexico, puedes reusar botellas si están más del 50 por ciento llenas y el volumen total se cumple.",
                confidence=0.9,
                drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
                audio_base64=None
            )

    elif "rapido" in question_lower or "velocidad" in question_lower:
        print(f"[FALLBACK KEYWORD MATCH] 'rapido/velocidad' matched")
        return VoiceResponse(
            answer="Pre-organiza los items únicos antes de empezar y usa ambas manos para items simétricos.",
            confidence=0.7,
            drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
            audio_base64=None
        )

    elif any(word in question_lower for word in ["vence", "expira", "caducidad", "expiration", "expired", "vencido", "vencimiento", "fechas"]):
        print(f"[FALLBACK KEYWORD MATCH] 'expiration' keywords matched")
        return VoiceResponse(
            answer="Descarta productos con menos de 5 a 7 días antes de la expiración. Es regla de seguridad de la cadena de frío. Nunca agregues al carrito si está vencido o próximo a vencer.",
            confidence=0.85,
            drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
            audio_base64=None
        )

    elif any(word in question_lower for word in ["agregado", "carrito", "inventory", "stock", "inventario"]):
        print(f"[FALLBACK KEYWORD MATCH] 'inventory/stock' keywords matched")
        return VoiceResponse(
            answer="Verifica primero la fecha de expiración antes de agregar cualquier producto. Solo agrega items con al menos 5 días de vida útil.",
            confidence=0.8,
            drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
            audio_base64=None
        )

    # Default fallback
    print(f"[FALLBACK KEYWORD MATCH] No keywords matched, using default fallback response")
    print(f"[FALLBACK RESPONSE] Question keywords: {question_lower}")
    return VoiceResponse(
        answer="No tengo suficiente información para responder esa pregunta. Por favor consulta el manual o pregunta a tu supervisor.",
        confidence=0.3,
        drawer_id=query.drawer_context.drawer_id if query.drawer_context else None,
        suggestions=["Reformula la pregunta", "Consulta el manual de procedimientos"],
        audio_base64=None
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
