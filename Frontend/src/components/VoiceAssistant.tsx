import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Select } from './ui/select';
import { Label } from './ui/label';
import { Mic, MicOff, Volume2, Copy, RotateCcw } from 'lucide-react';
import { apiService, type DrawerContext, type VoiceResponse } from '../services/api';

// Web Speech API type definitions
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  isFinal: boolean;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

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

export function VoiceAssistant() {
  // State management
  const [selectedDrawer, setSelectedDrawer] = useState<string>('DRW_001');
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [responseReceived, setResponseReceived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [browserSupport, setBrowserSupport] = useState(true);

  // Refs
  const recognitionRef = useRef<any>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

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
      setIsListening(true);
      setTranscript('');
      setError(null);
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
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
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    synthRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  // Auto-scroll conversation to bottom
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  // Start listening
  const startListening = () => {
    if (!recognitionRef.current) return;
    setTranscript('');
    recognitionRef.current.start();
  };

  // Stop listening
  const stopListening = () => {
    if (!recognitionRef.current) return;
    recognitionRef.current.stop();
  };

  // Handle voice query submission
  const handleVoiceQuery = async () => {
    if (!transcript.trim()) {
      setError('Por favor di algo primero.');
      return;
    }

    const question = transcript;
    setTranscript('');
    setResponseReceived(false);
    setIsLoading(true);
    setError(null);

    // Add user message to conversation
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

      // Call voice assistant API using service
      const data = await apiService.voiceAssistantQuery({
        question: question,
        drawer_context: drawerData
      });

      // Add assistant message to conversation
      const assistantMessage: ConversationMessage = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date()
      };
      setConversation(prev => [...prev, assistantMessage]);

      // Speak the response
      speakResponse(data.answer);
      setResponseReceived(true);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error al procesar la pregunta';
      setError(`Error: ${errorMsg}`);
      setIsLoading(false);
    }
  };

  // Text-to-speech function
  const speakResponse = (text: string) => {
    if (!synthRef.current) {
      setError('Text-to-speech no está disponible');
      setIsLoading(false);
      return;
    }

    // Cancel any ongoing speech
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onend = () => {
      setIsLoading(false);
    };

    utterance.onerror = () => {
      setError('Error al hablar la respuesta');
      setIsLoading(false);
    };

    synthRef.current.speak(utterance);
  };

  // Clear conversation
  const clearConversation = () => {
    setConversation([]);
    setTranscript('');
    setError(null);
    setResponseReceived(false);
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
          <div className="p-4 bg-red-50 text-red-700 rounded-lg">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentDrawer = SAMPLE_DRAWERS[selectedDrawer];

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="w-5 h-5" />
            Asistente de Voz para Productividad
          </CardTitle>
          <CardDescription>
            Activa el micrófono y formula preguntas sobre el drawer actual. El asistente te responderá por voz.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Drawer Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Información del Drawer</CardTitle>
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
            <div className="grid grid-cols-2 gap-4 p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="text-sm font-semibold text-slate-600">Categoría</p>
                <p className="text-sm">{currentDrawer.category}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-600">Aerolínea</p>
                <Badge>{currentDrawer.airline}</Badge>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-600">Total de Items</p>
                <p className="text-sm">{currentDrawer.total_items}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-600">Tipos Únicos</p>
                <p className="text-sm">{currentDrawer.unique_item_types}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Voice Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Control de Voz</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Transcript Display */}
          <div className="space-y-2">
            <Label>Pregunta detectada:</Label>
            <div className="p-3 bg-slate-100 rounded-lg min-h-12 flex items-center">
              {isListening && <span className="text-slate-500 italic">Escuchando...</span>}
              {!isListening && transcript && <span>{transcript}</span>}
              {!isListening && !transcript && <span className="text-slate-400 italic">Tu pregunta aparecerá aquí...</span>}
            </div>
          </div>

          {/* Microphone Buttons */}
          <div className="flex gap-3">
            <Button
              onClick={startListening}
              disabled={isListening || isLoading}
              className="flex-1 gap-2 h-12 text-base"
              variant="default"
            >
              <Mic className="w-5 h-5" />
              Activar Micrófono
            </Button>

            <Button
              onClick={stopListening}
              disabled={!isListening || isLoading}
              className="flex-1 gap-2 h-12 text-base"
              variant="destructive"
            >
              <MicOff className="w-5 h-5" />
              Detener
            </Button>
          </div>

          {/* Submit Question Button */}
          {transcript && (
            <Button
              onClick={handleVoiceQuery}
              disabled={isLoading || !transcript.trim()}
              className="w-full gap-2 h-12 text-base"
              variant="secondary"
            >
              <Volume2 className="w-5 h-5" />
              {isLoading ? 'Procesando...' : 'Enviar Pregunta'}
            </Button>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Conversation History */}
      <Card className="h-96 flex flex-col">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg">Historial de Conversación</CardTitle>
            <Button
              onClick={clearConversation}
              variant="ghost"
              size="sm"
              className="gap-1"
            >
              <RotateCcw className="w-4 h-4" />
              Limpiar
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto space-y-3">
          {conversation.length === 0 ? (
            <p className="text-slate-400 text-center py-8">
              Haz una pregunta sobre el drawer para empezar...
            </p>
          ) : (
            conversation.map((msg, idx) => (
              <div key={idx} className={`space-y-1 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                <Badge variant={msg.role === 'user' ? 'default' : 'secondary'}>
                  {msg.role === 'user' ? 'Tú' : 'Asistente'}
                </Badge>
                <p className={`p-3 rounded-lg text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-100 text-blue-900'
                    : 'bg-green-100 text-green-900'
                }`}>
                  {msg.content}
                </p>
                <p className="text-xs text-slate-500">
                  {msg.timestamp.toLocaleTimeString('es-ES')}
                </p>
              </div>
            ))
          )}
          <div ref={conversationEndRef} />
        </CardContent>

        {/* Copy Button */}
        {conversation.filter(m => m.role === 'assistant').length > 0 && (
          <div className="p-3 border-t">
            <Button
              onClick={copyLastResponse}
              variant="ghost"
              size="sm"
              className="w-full gap-2"
            >
              <Copy className="w-4 h-4" />
              Copiar Última Respuesta
            </Button>
          </div>
        )}
      </Card>

      {/* Quick Examples */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Preguntas de Ejemplo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <p className="text-sm text-slate-600">• "¿Dónde pongo el CUTL01?"</p>
            <p className="text-sm text-slate-600">• "¿Puedo reusar esta botella a la mitad?"</p>
            <p className="text-sm text-slate-600">• "¿Cuál es la complejidad de este drawer?"</p>
            <p className="text-sm text-slate-600">• "¿Qué debo verificar antes de empacar?"</p>
            <p className="text-sm text-slate-600">• "¿Hay restricciones de empaque?"</p>
            <p className="text-sm text-slate-600">• "¿Cuánto tiempo tarda este drawer?"</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
