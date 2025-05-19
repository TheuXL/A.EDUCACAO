import React from 'react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { SearchResult } from '@/services/api';

// Ícones para os diferentes tipos de conteúdo
function DocumentIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
    </svg>
  );
}

function VideoIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
    </svg>
  );
}

function ImageIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
    </svg>
  );
}

function JsonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
    </svg>
  );
}

function AudioIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
    </svg>
  );
}

function MarkdownIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 3a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H7z" clipRule="evenodd" />
    </svg>
  );
}

// Função para obter o ícone correto com base no tipo
function getContentIcon(type: string) {
  switch(type) {
    case 'pdf':
      return <DocumentIcon />;
    case 'text':
      return <MarkdownIcon />;
    case 'video':
      return <VideoIcon />;
    case 'image':
      return <ImageIcon />;
    case 'audio':
      return <AudioIcon />;
    case 'json':
      return <JsonIcon />;
    default:
      return <DocumentIcon />;
  }
}

// Função para formatar o tipo de conteúdo
function formatContentType(type: string) {
  switch(type) {
    case 'pdf':
      return 'PDF';
    case 'text':
      return 'Texto';
    case 'video':
      return 'Vídeo';
    case 'image':
      return 'Imagem';
    case 'audio':
      return 'Áudio';
    case 'json':
      return 'Exercício';
    default:
      return type.toUpperCase();
  }
}

// Função para formatar o tamanho do arquivo
function formatFileSize(bytes?: number) {
  if (!bytes) return '';
  
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 Byte';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i)) + ' ' + sizes[i];
}

// Função para formatar a duração
function formatDuration(seconds?: number) {
  if (!seconds) return '';
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Função para detectar o tipo de arquivo pela extensão
function detectFileType(source?: string): string | null {
  if (!source) return null;
  
  const extension = source.toLowerCase().split('.').pop();
  
  if (['mp4', 'avi', 'mov', 'mkv'].includes(extension || '')) {
    return 'video';
  } else if (['mp3', 'wav', 'ogg', 'aac', 'm4a'].includes(extension || '')) {
    return 'audio';
  } else if (['jpg', 'jpeg', 'png', 'gif'].includes(extension || '')) {
    return 'image';
  } else if (['md', 'txt'].includes(extension || '')) {
    return 'text';
  } else if (['pdf'].includes(extension || '')) {
    return 'pdf';
  }
  
  return null;
}

interface ContentCardProps {
  content: SearchResult;
  onSelect: () => void;
}

export function ContentCard({ content, onSelect }: ContentCardProps) {
  const { id, type, content_preview, metadata } = content;
  const title = metadata.title || 'Conteúdo sem título';
  
  // Detecta o tipo de arquivo baseado na fonte, se disponível
  const fileType = metadata.source ? detectFileType(metadata.source) || type : type;
  
  return (
    <Card className="transition-all duration-300 hover:shadow-md">
      <CardHeader className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-blue-100 rounded-full text-blue-600">
            {getContentIcon(fileType)}
          </div>
          <h3 className="font-medium text-gray-900 truncate max-w-md">{title}</h3>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {formatContentType(fileType)}
        </span>
      </CardHeader>
      
      <CardContent>
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {content_preview}
        </p>
        
        {/* Metadados adicionais */}
        <div className="flex items-center text-sm text-gray-500 space-x-4 mt-3">
          {metadata.size_bytes && (
            <div className="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{formatFileSize(metadata.size_bytes)}</span>
            </div>
          )}
          
          {metadata.pages && (
            <div className="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <span>{metadata.pages} {metadata.pages === 1 ? 'página' : 'páginas'}</span>
            </div>
          )}
          
          {metadata.duration_seconds && (
            <div className="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{formatDuration(metadata.duration_seconds)}</span>
            </div>
          )}
          
          {metadata.source && (
            <div className="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="truncate max-w-[100px]" title={metadata.source}>
                {metadata.source.split('/').pop()}
              </span>
            </div>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex justify-end">
        <Button 
          variant="primary" 
          size="sm" 
          onClick={onSelect}
        >
          Ver Conteúdo
        </Button>
      </CardFooter>
    </Card>
  );
} 