import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Select } from './ui/select';
import { Label } from './ui/label';
import { Copy, RotateCcw, Settings } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { VoiceOrb, type VoiceOrbState } from './VoiceOrb';
import { ConversationBubbles } from './ConversationBubbles';
import { apiService, type DrawerContext, type VoiceResponse } from '../services/api';

type SpeechRecognitionErrorCode = 'no-speech' | 'audio-capture' | 'network' | 'aborted' | 'service-not-allowed' | 'bad-grammar' | 'network-timeout';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SAMPLE_DRAWERS: Record<string, DrawerContext> = {
  DRW_001: {
    drawer_id: 'DRW_001',
    flight_type: 'Long-Haul',
    category: 'Beverage',
    total_items: 12,
    unique_item_types: 6,
    item_list: 'CUTL01, CUP01, CUP02, DRK01, DRK02, DRK03, SNK01, SNK02, SNK03, SNK04, SNK05, DRK05',
    airline: 'Aeromexico',
    contract_id: 'AERO-2024-001'
  },
  DRW_006: {
    drawer_id: 'DRW_006',
    flight_type: 'Short-Haul',
    category: 'Breakfast',
    total_items: 15,
    unique_item_types: 8,
    item_list: 'CUTL01, CUTL02, CUP01, CUP02, SNK01, SNK02, SNK03, SNK04, DRK01, DRK02, DRK03, DRK04, DRK05, SPOON01, NAPK01',
    airline: 'Delta',
    contract_id: 'DLT-2024-002'
  },
  DRW_010: {
    drawer_id: 'DRW_010',
    flight_type: 'Long-Haul',
    category: 'Meal',
    total_items: 18,
    unique_item_types: 9,
    item_list: 'PLATE01, FORK01, KNIFE01, CUTL01, CUP01, CUP02, DRK01, DRK02, DRK03, DRK04, SNK01, SNK02, SNK03, SNK04, SNK05, NAPK01, NAPK02, TRAY01',
    airline: 'United',
    contract_id: 'UTD-2024-003'
  }
};

export function VoiceAssistantModern() {
  // State management
  const [selectedDrawer, setSelectedDrawer] = useState<string>('DRW_001');
  const [orbState, setOrbState] = useState<VoiceOrbState>('idle');
  const [transcript, setTranscript] = useState('');
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [browserSupport, setBrowserSupport] = useState(true);
  const [showDrawerInfo, setShowDrawerInfo] = useState(false);
  const [isLoadingResponse, setIsLoadingResponse] = useState(false);

  // Refs
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const transcriptRef = useRef<string>('');

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.webkitSpeechRecognition || (window as any).SpeechRecognition;

    if (!SpeechRecognition) {
      setBrowserSupport(false);
      setError('Tu navegador no soporta Web Speech API. Por favor usa Chrome, Edge o Safari.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'es-ES';

    recognition.onstart = () => {
      setOrbState('listening');
      transcriptRef.current = '';
      setTranscript('');
      setError(null);
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          transcriptRef.current = transcript;
          setTranscript(transcript);
        } else {
          interimTranscript += transcript;
        }
      }

      if (interimTranscript) {
        setTranscript(interimTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      const errorMessages: Record<SpeechRecognitionErrorCode, string> = {
        'no-speech': 'No se detectó voz. Por favor intenta de nuevo.',
        'audio-capture': 'No se pudo acceder al micrófono. Verifica los permisos.',
        'network': 'Error de conexión. Intenta más tarde.',
        'aborted': 'El reconocimiento fue cancelado.',
        'service-not-allowed': 'El servicio de reconocimiento no está disponible.',
        'bad-grammar': 'Error al procesar el audio.',
        'network-timeout': 'Se agotó el tiempo de espera.'
      };

      const errorMsg = errorMessages[event.error as SpeechRecognitionErrorCode] || 'Error desconocido en reconocimiento de voz.';
      setError(errorMsg);
      setOrbState('idle');
    };

    recognition.onend = () => {
      // Don't change state here - let handleOrbToggle manage it
    };

    recognitionRef.current = recognition;
    synthRef.current = window.speechSynthesis;
  }, []);

  // Handle orb toggle (single click to start/stop)
  const handleOrbToggle = async () => {
    if (orbState === 'idle') {
      // Start listening
      if (!recognitionRef.current) return;
      transcriptRef.current = '';
      setTranscript('');
      recognitionRef.current.start();
    } else if (orbState === 'listening') {
      // Stop listening and submit
      if (!recognitionRef.current) return;
      recognitionRef.current.stop();

      // Use transcriptRef to get the final transcript
      const finalTranscript = transcriptRef.current.trim();

      if (finalTranscript) {
        // Submit the question immediately
        await submitQuestion(finalTranscript);
      } else {
        setOrbState('idle');
      }
    }
  };

  // Submit question
  const submitQuestion = async (question: string) => {
    setTranscript('');
    setOrbState('processing');
    setIsLoadingResponse(true);
    setError(null);

    // Add user message
    const userMessage: ConversationMessage = {
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    setConversation(prev => [...prev, userMessage]);

    try {
      const drawerData = SAMPLE_DRAWERS[selectedDrawer];
      if (!drawerData) {
        throw new Error('Drawer no encontrado');
      }

      const response = await apiService.voiceAssistantQuery({
        question: question,
        drawer_context: drawerData
      });

      const assistantMessage: ConversationMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date()
      };
      setConversation(prev => [...prev, assistantMessage]);

      // Speak response
      speakResponse(response.answer);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error al procesar la pregunta';
      setError(`Error: ${errorMsg}`);
      setOrbState('idle');
      setIsLoadingResponse(false);
    }
  };

  // Text-to-speech
  const speakResponse = (text: string) => {
    if (!synthRef.current) {
      setError('Text-to-speech no está disponible');
      setOrbState('idle');
      setIsLoadingResponse(false);
      return;
    }

    synthRef.current.cancel();
    setOrbState('speaking');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onend = () => {
      setOrbState('idle');
      setIsLoadingResponse(false);
    };

    utterance.onerror = () => {
      setError('Error al hablar la respuesta');
      setOrbState('idle');
      setIsLoadingResponse(false);
    };

    synthRef.current.speak(utterance);
  };

  // Clear conversation
  const clearConversation = () => {
    setConversation([]);
    setTranscript('');
    setError(null);
  };

  // Copy last response
  const copyLastResponse = () => {
    const lastMessage = conversation.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      navigator.clipboard.writeText(lastMessage.content);
    }
  };

  if (!browserSupport) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Asistente de Voz</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-red-50 text-red-700 rounded-lg">{error}</div>
        </CardContent>
      </Card>
    );
  }

  const currentDrawer = SAMPLE_DRAWERS[selectedDrawer];
  const complexity = ((currentDrawer.unique_item_types / currentDrawer.total_items) * 100).toFixed(0);

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <motion.header
        className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-40"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Asistente de Voz</h1>
              <p className="text-sm text-slate-500">Drawer {selectedDrawer}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDrawerInfo(!showDrawerInfo)}
              className="gap-2"
            >
              <Settings className="w-4 h-4" />
              Configuración
            </Button>
          </div>
        </div>
      </motion.header>

      {/* Main content */}
      <motion.main
        className="container mx-auto px-4 py-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Drawer selector - collapsible */}
          <AnimatePresence>
            {showDrawerInfo && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <Card className="border-blue-200 bg-blue-50">
                  <CardHeader>
                    <CardTitle className="text-lg">Configuración del Drawer</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="drawer-select">Selecciona un Drawer</Label>
                      <Select
                        value={selectedDrawer}
                        onValueChange={setSelectedDrawer}
                      >
                        {Object.entries(SAMPLE_DRAWERS).map(([id, drawer]) => (
                          <option key={id} value={id}>
                            {id} - {drawer.category} ({drawer.airline})
                          </option>
                        ))}
                      </Select>
                    </div>

                    {currentDrawer && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-white rounded-lg">
                        <div>
                          <p className="text-xs font-semibold text-slate-600">Categoría</p>
                          <Badge className="mt-1">{currentDrawer.category}</Badge>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-slate-600">Aerolínea</p>
                          <Badge variant="secondary" className="mt-1">{currentDrawer.airline}</Badge>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-slate-600">Total Items</p>
                          <p className="text-sm font-mono">{currentDrawer.total_items}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-slate-600">Complejidad</p>
                          <p className="text-sm font-mono">{complexity}%</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main voice interaction area */}
          <div className="relative">
            {/* Voice Orb with background */}
            <div className="flex flex-col items-center justify-center py-16">
              <VoiceOrb
                state={orbState}
                onToggle={handleOrbToggle}
                isDisabled={orbState === 'processing' || orbState === 'speaking'}
              />
            </div>

            {/* Error display */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Conversation area */}
          <Card className="border-2 bg-white">
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Conversación</CardTitle>
                  <CardDescription>Historial de preguntas y respuestas</CardDescription>
                </div>
                <Button
                  onClick={clearConversation}
                  variant="ghost"
                  size="sm"
                  className="gap-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  Limpiar
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="max-h-96 overflow-y-auto pr-2">
                <ConversationBubbles
                  messages={conversation}
                  isLoading={isLoadingResponse}
                />
              </div>
            </CardContent>
          </Card>

          {/* Copy button */}
          {conversation.filter(m => m.role === 'assistant').length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-center"
            >
              <Button
                onClick={copyLastResponse}
                variant="outline"
                className="gap-2 px-6"
              >
                <Copy className="w-4 h-4" />
                Copiar Última Respuesta
              </Button>
            </motion.div>
          )}

          {/* Quick tips */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-indigo-50 to-blue-50 p-6 rounded-lg border border-indigo-200"
          >
            <h3 className="font-semibold text-indigo-900 mb-3">Consejos de Uso</h3>
            <ul className="space-y-2 text-sm text-indigo-800">
              <li>✨ Pulsa el círculo y mantén para hablar</li>
              <li>✨ Suelta para enviar tu pregunta</li>
              <li>✨ El asistente te responde por voz automáticamente</li>
              <li>✨ Cambia de drawer para obtener respuestas específicas</li>
            </ul>
          </motion.div>
        </div>
      </motion.main>
    </div>
  );
}
