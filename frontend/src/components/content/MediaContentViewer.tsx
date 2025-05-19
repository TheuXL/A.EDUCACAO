import React, { useState, useEffect } from 'react';
import { validateMediaUrl } from '@/utils/mediaUtils';
import { MediaFormat } from './MediaFormatSelector';

interface MediaContentViewerProps {
  format: MediaFormat;
  filePath?: string;
  onError?: (message: string) => void;
}

export function MediaContentViewer({ 
  format, 
  filePath,
  onError 
}: MediaContentViewerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    setError(null);

    // Default media paths based on format
    const defaultPaths: Record<MediaFormat, string> = {
      video: 'videos/Dica do professor.mp4',
      audio: 'audio/Dica do professor.mp3',
      image: 'images/Infografico-1.jpg',
      text: 'text/Capítulo do Livro.txt',
      exercises: 'text/Exercícios.txt',
      mixed: 'videos/Dica do professor.mp4' // Default for mixed is video
    };

    try {
      // Use provided filePath or default path
      const path = filePath || defaultPaths[format];
      const url = validateMediaUrl(path);
      setMediaUrl(url);
      setIsLoading(false);
    } catch (err) {
      const errorMessage = `Erro ao carregar conteúdo ${format}: ${err instanceof Error ? err.message : 'Erro desconhecido'}`;
      setError(errorMessage);
      if (onError) onError(errorMessage);
      setIsLoading(false);
    }
  }, [format, filePath, onError]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !mediaUrl) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
        <p>{error || 'Não foi possível carregar o conteúdo solicitado.'}</p>
      </div>
    );
  }

  // Render different content based on format
  switch (format) {
    case 'video':
      return (
        <div className="bg-black rounded-lg overflow-hidden">
          <div className="relative pt-[56.25%]">
            <video
              className="absolute top-0 left-0 w-full h-full"
              controls
              autoPlay={false}
              preload="metadata"
              src={mediaUrl}
            >
              <p>Seu navegador não suporta a reprodução de vídeos.</p>
              <a href={mediaUrl} target="_blank" rel="noopener noreferrer">
                Baixar vídeo
              </a>
            </video>
          </div>
        </div>
      );

    case 'audio':
      return (
        <div className="bg-white p-4 rounded-lg shadow">
          <audio
            className="w-full"
            controls
            autoPlay={false}
            preload="metadata"
            src={mediaUrl}
          >
            <p>Seu navegador não suporta a reprodução de áudio.</p>
            <a href={mediaUrl} target="_blank" rel="noopener noreferrer">
              Baixar áudio
            </a>
          </audio>
        </div>
      );

    case 'image':
      return (
        <div className="flex justify-center">
          <img
            src={mediaUrl}
            alt="Conteúdo visual"
            className="max-w-full max-h-[500px] rounded shadow"
          />
        </div>
      );

    case 'text':
      return (
        <div className="bg-white p-4 rounded-lg shadow">
          <p className="text-gray-700 mb-4">
            Documento de texto disponível para visualização.
          </p>
          <a 
            href={mediaUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
            </svg>
            Abrir Documento
          </a>
        </div>
      );

    case 'exercises':
      return (
        <div className="bg-white p-4 rounded-lg shadow">
          <p className="text-gray-700 mb-4">
            Exercícios práticos para testar seu conhecimento.
          </p>
          <a 
            href={mediaUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3z" />
              <path d="M3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zm5.99 7.176A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
            </svg>
            Iniciar Exercícios
          </a>
        </div>
      );

    case 'mixed':
      // For mixed format, default to video but could be enhanced to show multiple formats
      return (
        <div className="bg-black rounded-lg overflow-hidden">
          <div className="relative pt-[56.25%]">
            <video
              className="absolute top-0 left-0 w-full h-full"
              controls
              autoPlay={false}
              preload="metadata"
              src={mediaUrl}
            >
              <p>Seu navegador não suporta a reprodução de vídeos.</p>
              <a href={mediaUrl} target="_blank" rel="noopener noreferrer">
                Baixar vídeo
              </a>
            </video>
          </div>
        </div>
      );

    default:
      return (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 p-4 rounded">
          <p>Formato de conteúdo não reconhecido.</p>
        </div>
      );
  }
} 