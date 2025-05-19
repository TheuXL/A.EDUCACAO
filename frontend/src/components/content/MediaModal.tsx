import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { MediaContentViewer } from './MediaContentViewer';
import { MediaFormat, MediaFormatSelector } from './MediaFormatSelector';
import { Button } from '@/components/ui/Button';

interface MediaModalProps {
  onClose: () => void;
  isOpen: boolean;
  initialFormat?: MediaFormat;
  availableFormats?: MediaFormat[];
  title?: string;
}

export function MediaModal({ 
  onClose, 
  isOpen, 
  initialFormat = 'video',
  availableFormats = ['video', 'audio', 'text', 'image', 'exercises'],
  title = 'Conteúdo Complementar'
}: MediaModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<MediaFormat>(initialFormat);
  const [error, setError] = useState<string | null>(null);

  const handleFormatSelect = (format: MediaFormat) => {
    setSelectedFormat(format);
    setError(null); // Reset error when changing format
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="lg">
      <div className="space-y-6">
        {/* Format selector */}
        <MediaFormatSelector 
          onSelectFormat={handleFormatSelect} 
          availableFormats={availableFormats} 
        />
        
        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <p>{error}</p>
          </div>
        )}
        
        {/* Media content */}
        <div className="mt-4">
          <MediaContentViewer 
            format={selectedFormat} 
            onError={handleError} 
          />
        </div>
        
        {/* Close button */}
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <Button onClick={onClose} variant="outline">
            Fechar
          </Button>
        </div>
      </div>
    </Modal>
  );
} 