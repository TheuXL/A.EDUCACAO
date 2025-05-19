import React, { useState, useEffect } from 'react';
import { AnalyzeResponse, RelatedContent, sendFeedback } from '../../services/api';
import { validateMediaUrl, getFileType } from '@/utils/mediaUtils';
import { Button } from '@/components/ui/Button';
import { MediaModal } from './MediaModal';
import { MediaFormat } from './MediaFormatSelector';

// ContentTypeIcon component to display icons based on content type
const ContentTypeIcon = ({ type, className = "" }: { type: string, className?: string }) => {
  switch (type.toLowerCase()) {
    case 'video':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
          <line x1="7" y1="2" x2="7" y2="22"></line>
          <line x1="17" y1="2" x2="17" y2="22"></line>
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <line x1="2" y1="7" x2="7" y2="7"></line>
          <line x1="2" y1="17" x2="7" y2="17"></line>
          <line x1="17" y1="17" x2="22" y2="17"></line>
          <line x1="17" y1="7" x2="22" y2="7"></line>
        </svg>
      );
    case 'audio':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 18v-6a9 9 0 0 1 18 0v6"></path>
          <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path>
        </svg>
      );
    case 'image':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
      );
    default:
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
      );
  }
};

interface AdaptiveResponseProps {
  data: AnalyzeResponse;
  onFeedback: (feedback: 'positive' | 'negative') => void;
  onSelectRelatedContent: (content: RelatedContent) => void;
  feedbackStatus?: 'pending' | 'submitted' | null;
  onSelectSuggestion: (suggestion: string) => void;
}

export function AdaptiveResponse({ 
  data, 
  onFeedback, 
  onSelectRelatedContent,
  feedbackStatus,
  onSelectSuggestion
}: AdaptiveResponseProps) {
  const [internalFeedbackSubmitted, setInternalFeedbackSubmitted] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [initialMediaFormat, setInitialMediaFormat] = useState<MediaFormat>('video');
  
  const feedbackSubmitted = feedbackStatus === 'submitted' || internalFeedbackSubmitted;
  
  // Determine available media formats based on response data
  const getAvailableFormats = (): MediaFormat[] => {
    const formats: MediaFormat[] = [];
    
    if (data.has_video_content) formats.push('video');
    if (data.has_audio_content) formats.push('audio');
    if (data.has_image_content) formats.push('image');
    
    // Always include text and exercises as options
    if (!formats.includes('text')) formats.push('text');
    if (!formats.includes('exercises')) formats.push('exercises');
    
    return formats;
  };
  
  // Set initial format based on primary_media_type
  useEffect(() => {
    if (data.primary_media_type && data.primary_media_type !== 'mixed') {
      setInitialMediaFormat(data.primary_media_type as MediaFormat);
    } else if (data.has_video_content) {
      setInitialMediaFormat('video');
    } else if (data.has_audio_content) {
      setInitialMediaFormat('audio');
    } else if (data.has_image_content) {
      setInitialMediaFormat('image');
    } else {
      setInitialMediaFormat('text');
    }
  }, [data]);
  
  const handleOpenModal = () => {
    setIsModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setIsModalOpen(false);
  };
  
  const handleFeedbackSubmit = async (feedback: 'positive' | 'negative') => {
    if (feedbackSubmitted || isSubmittingFeedback) return;
    
    setIsSubmittingFeedback(true);
    
    try {
      const feedbackText = feedback === 'positive' ? 'positivo' : 'negativo';
      
      await sendFeedback(data.user_id, data.query_id || '', feedbackText);
      
      onFeedback(feedback);
      
      if (feedbackStatus === undefined) {
        setInternalFeedbackSubmitted(true);
      }
    } catch (error) {
      console.error('Erro ao enviar feedback:', error);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  
  // Extrai o caminho do arquivo da resposta
  const extractFilePath = (text: string): string | null => {
    // Procura pelo formato especial de comentário HTML com caminho de arquivo
    const filePathMatch = text.match(/<!-- file_path: (.*?) -->/);
    if (filePathMatch && filePathMatch[1]) {
      console.log("Arquivo encontrado via comentário HTML:", filePathMatch[1]);
      return filePathMatch[1];
    }
    
    // Procura por linha "Arquivo:" com caminho absoluto ou relativo
    const fileLineMatch = text.match(/(?:Arquivo|File):\s*(\/[^\s\n]+|[a-zA-Z]:[\\\/][^\s\n]+|[^\s\n]+\.[a-zA-Z0-9]{2,4})/i);
    if (fileLineMatch && fileLineMatch[1]) {
      console.log("Arquivo encontrado via linha 'Arquivo:':", fileLineMatch[1]);
      return fileLineMatch[1];
    }
    
    // Busca por padrões específicos de mídia
    const patterns = [
      // Vídeos
      { regex: /\(?(?:Video|Vídeo):\s*(.*?\.(?:mp4|avi|mov|mkv|webm))\)?/i, type: 'video' },
      { regex: /Arquivo[^:]*:\s*(.*?\.(?:mp4|avi|mov|mkv|webm))/i, type: 'video' },
      { regex: /(\/processed_data\/videos\/[^"\s\n]+)/i, type: 'video' },
      { regex: /(videos\/[^"\s\n]+\.(?:mp4|avi|mov|mkv|webm))/i, type: 'video' },
      
      // Áudios
      { regex: /\(?(?:Audio|Áudio):\s*(.*?\.(?:mp3|wav|ogg|aac|m4a))\)?/i, type: 'audio' },
      { regex: /Arquivo[^:]*:\s*(.*?\.(?:mp3|wav|ogg|aac|m4a))/i, type: 'audio' },
      { regex: /(\/processed_data\/audio\/[^"\s\n]+)/i, type: 'audio' },
      { regex: /(audio\/[^"\s\n]+\.(?:mp3|wav|ogg|aac|m4a))/i, type: 'audio' },
      
      // Imagens
      { regex: /\(?(?:Imagem|Image):\s*(.*?\.(?:jpg|jpeg|png|gif|svg|webp))\)?/i, type: 'image' },
      { regex: /Arquivo[^:]*:\s*(.*?\.(?:jpg|jpeg|png|gif|svg|webp))/i, type: 'image' },
      { regex: /(\/processed_data\/images\/[^"\s\n]+)/i, type: 'image' },
      { regex: /(images\/[^"\s\n]+\.(?:jpg|jpeg|png|gif|svg|webp))/i, type: 'image' },
      
      // Exercícios
      { regex: /\(?(?:Exercícios|Exercicios|Exercises):\s*(.*?\.(?:json|txt))\)?/i, type: 'exercises' },
      { regex: /Arquivo[^:]*:\s*(.*?\.(?:json))/i, type: 'exercises' },
      { regex: /(\/processed_data\/text\/Exercícios\.(?:txt|json))/i, type: 'exercises' },
      { regex: /(text\/Exercícios\.(?:txt|json))/i, type: 'exercises' },
      
      // Textos
      { regex: /\(?(?:Texto|Text):\s*(.*?\.(?:txt|md|pdf))\)?/i, type: 'text' },
      { regex: /(\/processed_data\/text\/[^"\s\n]+)/i, type: 'text' },
      { regex: /(text\/[^"\s\n]+\.(?:txt|md|pdf))/i, type: 'text' },
    ];
    
    // Tenta encontrar correspondências para cada padrão
    for (const pattern of patterns) {
      const match = text.match(pattern.regex);
      if (match && match[1]) {
        console.log(`Arquivo de ${pattern.type} encontrado:`, match[1]);
        return match[1];
      }
    }
    
    // Verifica se há um caminho de arquivo diretamente na propriedade file_path da resposta
    if (data.file_path) {
      console.log("Arquivo encontrado via propriedade file_path:", data.file_path);
      return data.file_path;
    }
    
    // Verifica se há um tipo de mídia principal definido e tenta inferir um arquivo padrão
    if (data.primary_media_type) {
      console.log("Tipo de mídia principal definido:", data.primary_media_type);
      
      // Arquivos padrão para cada tipo de mídia
      const defaultFiles = {
        video: 'videos/Dica do professor.mp4',
        audio: 'audio/Dica do professor.mp3',
        image: 'images/Infografico-1.jpg',
        text: 'text/Apresentação.txt',
        exercises: 'text/Exercícios.txt'
      };
      
      const mediaType = data.primary_media_type.toLowerCase();
      if (defaultFiles[mediaType as keyof typeof defaultFiles]) {
        console.log("Usando arquivo padrão para o tipo:", mediaType);
        return defaultFiles[mediaType as keyof typeof defaultFiles];
      }
    }
    
    return null;
  };
  
  const formatResponse = (text: string) => {
    const isApproximateResponse = text.includes('Não sei responder exatamente sua pergunta') || 
                                  text.includes('provável resposta baseada nos recursos disponíveis');
    
    if (!text || text.trim() === '') {
      return [
        <div key="error" className="text-red-600 dark:text-red-400">
          Não foi possível carregar a resposta. Por favor, tente novamente.
        </div>
      ];
    }

    // Remove os marcadores de caminho de arquivo
    const cleanedText = text.replace(/<!-- file_path: (.*?) -->/g, '');

    try {
      if (cleanedText.trim().startsWith('{') && cleanedText.trim().endsWith('}')) {
        const jsonData = JSON.parse(cleanedText);
        if (jsonData.response) {
          text = jsonData.response;
        }
      }
    } catch (e) {
      console.log('Resposta não está em formato JSON válido');
    }

    return cleanedText
      .split('\n')
      .map((line, index) => {
        // Ignora linhas de comentário HTML
        if (line.trim().startsWith('<!--') && line.trim().endsWith('-->')) {
          return null;
        }
        
        // Títulos e seções
        if (line.startsWith('✅') || line.startsWith('📌') || line.startsWith('📂') || 
            line.startsWith('💡') || line.startsWith('📚') || line.startsWith('🧐') ||
            line.startsWith('📄') || line.startsWith('📺') || line.startsWith('🖼️') || 
            line.startsWith('🔊')) {
          return (
            <h3 key={index} className="font-semibold text-lg mt-3 mb-2 text-gray-900">
              {line}
            </h3>
          );
        }
        
        // Listas não ordenadas
        if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
          return (
            <div key={index} className="flex items-start my-1">
              <span className="mr-2">•</span>
              <span>{line.trim().substring(2)}</span>
            </div>
          );
        }
        
        // Listas ordenadas (números)
        if (/^\d+\.\s/.test(line.trim())) {
          const number = line.trim().match(/^(\d+)\.\s/)?.[1];
          return (
            <div key={index} className="flex items-start my-1">
              <span className="mr-2 font-medium">{number}.</span>
              <span>{line.trim().substring(number!.length + 2)}</span>
            </div>
          );
        }
        
        // Linhas em branco
        if (line.trim() === '') {
          return <div key={index} className="h-4"></div>;
        }
        
        // Linhas normais
        return <p key={index} className="my-2">{line}</p>;
      })
      .filter(Boolean);
  };
  
  // Renderiza o conteúdo do arquivo
  const renderFileContent = () => {
    // Primeiro, tentamos extrair o caminho do arquivo da resposta
    const filePath = extractFilePath(data.response);
    
    // Vamos tentar detectar múltiplos tipos de mídia
    const defaultMedia = {
      video: data.primary_media_type === 'video' ? 'videos/Dica do professor.mp4' : null,
      audio: data.primary_media_type === 'audio' ? 'audio/Dica do professor.mp3' : null,
      image: data.primary_media_type === 'image' ? 'images/Infografico-1.jpg' : null,
      exercises: data.primary_media_type === 'exercises' ? 'text/Exercícios.txt' : null,
      text: data.primary_media_type === 'text' ? 'text/Capítulo do Livro.txt' : null
    };
    
    // Se o tipo de mídia principal for 'mixed', mostramos todos os tipos disponíveis
    if (data.primary_media_type === 'mixed' || !data.primary_media_type) {
      // Vamos mostrar os tipos de mídia padrão para conteúdo misto
      return (
        <>
          {renderVideoContent('videos/Dica do professor.mp4')}
          {renderAudioContent('audio/Dica do professor.mp3')}
          {renderImageContent('images/Infografico-1.jpg')}
          {renderExercisesContent('text/Exercícios.txt')}
          {filePath && renderContentByType(filePath)}
        </>
      );
    }
    
    // Se temos um caminho de arquivo específico, renderizamos com base no tipo
    if (filePath) {
      return renderContentByType(filePath);
    }
    
    // Se temos um tipo de mídia principal definido, usamos o arquivo padrão para esse tipo
    if (data.primary_media_type && defaultMedia[data.primary_media_type as keyof typeof defaultMedia]) {
      const mediaPath = defaultMedia[data.primary_media_type as keyof typeof defaultMedia]!;
      return renderContentByType(mediaPath);
    }
    
    // Se não encontramos nada, não renderizamos nada
    return null;
  };
  
  // Função auxiliar para renderizar conteúdo com base no tipo de arquivo
  const renderContentByType = (filePath: string) => {
    const fileType = getFileType(filePath);
    console.log("Tipo de arquivo detectado:", fileType, "para o caminho:", filePath);
    
    switch (fileType) {
      case 'video':
        return renderVideoContent(filePath);
      case 'audio':
        return renderAudioContent(filePath);
      case 'image':
        return renderImageContent(filePath);
      case 'exercises':
        return renderExercisesContent(filePath);
      case 'markdown':
        return renderMarkdownContent(filePath);
      default:
        return null;
    }
  };
  
  const renderVideoContent = (filePath: string = '') => {
    if (!filePath) return null;
    
    const videoUrl = validateMediaUrl(filePath);
    
    return (
      <div className="mt-4 mb-6">
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
          <h3 className="text-lg font-medium mb-3 flex items-center">
            <ContentTypeIcon type="video" className="mr-2 text-blue-600" />
            Conteúdo em Vídeo
          </h3>
          <div className="relative pt-[56.25%] rounded overflow-hidden bg-black">
            <video
              className="absolute top-0 left-0 w-full h-full"
              controls
              preload="metadata"
              src={videoUrl}
            >
              <p>Seu navegador não suporta a reprodução de vídeos.</p>
              <a href={videoUrl} target="_blank" rel="noopener noreferrer">
                Baixar vídeo
              </a>
            </video>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            <a 
              href={videoUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Abrir em nova janela
            </a>
          </div>
        </div>
      </div>
    );
  };
  
  const renderImageContent = (filePath: string = '') => {
    if (!filePath) return null;
    
    const imageUrl = validateMediaUrl(filePath);
    
    return (
      <div className="mt-4 mb-6">
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
          <h3 className="text-lg font-medium mb-3 flex items-center">
            <ContentTypeIcon type="image" className="mr-2 text-green-600" />
            Imagem Ilustrativa
          </h3>
          <div className="flex justify-center">
            <img
              src={imageUrl}
              alt="Imagem relacionada ao conteúdo"
              className="max-w-full max-h-[500px] rounded shadow"
            />
          </div>
          <div className="mt-2 text-sm text-gray-600 text-center">
            <a 
              href={imageUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Ver imagem em tamanho completo
            </a>
          </div>
        </div>
      </div>
    );
  };
  
  const renderAudioContent = (filePath: string = '') => {
    if (!filePath) return null;
    
    const audioUrl = validateMediaUrl(filePath);
    
    return (
      <div className="mt-4 mb-6">
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
          <h3 className="text-lg font-medium mb-3 flex items-center">
            <ContentTypeIcon type="audio" className="mr-2 text-purple-600" />
            Conteúdo em Áudio
          </h3>
          <div className="bg-white p-3 rounded shadow">
            <audio
              controls
              className="w-full"
              preload="metadata"
              src={audioUrl}
            >
              <p>Seu navegador não suporta a reprodução de áudio.</p>
              <a href={audioUrl} target="_blank" rel="noopener noreferrer">
                Baixar áudio
              </a>
            </audio>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            <a 
              href={audioUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Abrir em nova janela
            </a>
          </div>
        </div>
      </div>
    );
  };
  
  const renderMarkdownContent = (filePath: string = '') => {
    if (!filePath) return null;
    
    const fileUrl = validateMediaUrl(filePath);
    
    return (
      <div className="mt-4 mb-6">
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
          <h3 className="text-lg font-medium mb-3 flex items-center">
            <ContentTypeIcon type="text" className="mr-2 text-gray-600" />
            Conteúdo Textual Complementar
          </h3>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-600 mb-2">
              Este conteúdo está disponível em um arquivo separado.
            </p>
            <a 
              href={fileUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
              </svg>
              Visualizar Documento
            </a>
          </div>
        </div>
      </div>
    );
  };
  
  const renderExercisesContent = (filePath: string = '') => {
    if (!filePath) return null;
    
    const exercisesUrl = validateMediaUrl(filePath);
    
    return (
      <div className="mt-4 mb-6">
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
          <h3 className="text-lg font-medium mb-3 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-orange-600" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
            Exercícios Práticos
          </h3>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-600 mb-2">
              Exercícios disponíveis para praticar o conteúdo.
            </p>
            <a 
              href={exercisesUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
              </svg>
              Acessar Exercícios
            </a>
          </div>
        </div>
      </div>
    );
  };
  
  // Extrai sugestões de consulta da resposta
  const renderSuggestions = (response: string) => {
    // Procura por sugestões no formato "Sugestões: item1, item2, item3"
    const suggestionsMatch = response.match(/Sugestões:?\s*(.*?)(?:\n\n|\n$|$)/i);
    
    if (!suggestionsMatch) return null;
    
    const suggestionsText = suggestionsMatch[1];
    const suggestions = suggestionsText
      .split(/,\s*/)
      .map(s => s.trim())
      .filter(s => s.length > 0);
    
    if (suggestions.length === 0) return null;
    
    return (
      <div className="mt-4 pt-3 border-t border-gray-200">
        <p className="text-sm font-medium text-white mb-2">Perguntas relacionadas:</p>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSelectSuggestion(suggestion)}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-full transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="text-white">
      <div className="prose prose-sm max-w-none text-white">
        {formatResponse(data.response)}
        {renderFileContent()}
        
        {/* Explore content button */}
        <div className="mt-6 flex justify-center">
          <Button 
            onClick={handleOpenModal}
            className="bg-blue-600 hover:bg-blue-700 text-white flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
            </svg>
            Explorar Conteúdo Completo
          </Button>
        </div>
      </div>
      
      {renderSuggestions(data.response)}
      
      {/* Feedback buttons */}
      <div className="mt-4 pt-3 border-t border-gray-200 flex justify-end">
        {feedbackSubmitted ? (
          <div className="text-sm text-white flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-green-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Obrigado pelo feedback
          </div>
        ) : (
          <div className="flex space-x-2">
            <button
              onClick={() => handleFeedbackSubmit('positive')}
              disabled={isSubmittingFeedback}
              className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-md transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
              Útil
            </button>
            <button
              onClick={() => handleFeedbackSubmit('negative')}
              disabled={isSubmittingFeedback}
              className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2" />
              </svg>
              Não útil
            </button>
          </div>
        )}
      </div>
      
      {/* Media Modal */}
      <MediaModal 
        isOpen={isModalOpen} 
        onClose={handleCloseModal} 
        initialFormat={initialMediaFormat}
        availableFormats={getAvailableFormats()}
        title="Aprofunde seu Conhecimento"
      />
    </div>
  );
} 