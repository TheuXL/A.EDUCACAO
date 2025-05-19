import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { uploadFiles } from '@/services/api';

export function FileUploader() {
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const fileList = Array.from(e.target.files);
      setFiles(fileList);
    }
  };
  
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const fileList = Array.from(e.dataTransfer.files);
      setFiles(fileList);
    }
  };
  
  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsLoading(true);
    setUploadResult(null);
    
    try {
      const result = await uploadFiles(files);
      
      if (result.success) {
        setUploadResult({
          success: true,
          message: `${result.uploaded_files.length} arquivo(s) indexado(s) com sucesso`
        });
      } else {
        setUploadResult({
          success: false,
          message: 'Erro ao indexar arquivos'
        });
      }
    } catch (err: any) {
      setUploadResult({
        success: false,
        message: err.message || 'Erro ao fazer upload dos arquivos'
      });
      console.error('Erro de upload:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const clearFiles = () => {
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  // Retorna ícone apropriado baseado na extensão do arquivo
  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return '🖼️';
      case 'mp4':
      case 'avi':
      case 'mov':
        return '🎬';
      case 'txt':
      case 'md':
        return '📃';
      case 'json':
        return '📊';
      default:
        return '📎';
    }
  };
  
  return (
    <Card className="w-full">
      <CardHeader>
        <h2 className="text-xl font-bold">Indexação de Conteúdo</h2>
        <p className="text-sm text-gray-600">Faça upload de arquivos para indexação e uso no sistema</p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <input
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
          ref={fileInputRef}
        />
        
        <div
          className={`border-2 border-dashed p-8 rounded-lg text-center ${
            files.length > 0 ? 'border-blue-300 bg-blue-50' : 'border-gray-300 hover:border-blue-300'
          }`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          {files.length === 0 ? (
            <div className="space-y-3">
              <div className="flex justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="text-gray-700">Arraste e solte arquivos aqui, ou clique para selecionar</p>
              <p className="text-gray-500 text-sm">Suporta PDF, DOC, TXT, imagens e vídeos</p>
            </div>
          ) : (
            <div className="text-left">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-medium text-gray-700">Arquivos selecionados: {files.length}</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    clearFiles();
                  }}
                >
                  Limpar
                </Button>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center p-2 bg-white rounded border border-gray-200">
                    <span className="mr-2 text-lg">{getFileIcon(file.name)}</span>
                    <div className="flex-grow">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {uploadResult && (
          <div 
            className={`p-3 rounded-md ${
              uploadResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}
          >
            {uploadResult.message}
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={clearFiles}
          disabled={files.length === 0 || isLoading}
        >
          Cancelar
        </Button>
        <Button
          variant="primary"
          onClick={handleUpload}
          disabled={files.length === 0 || isLoading}
          isLoading={isLoading}
        >
          {isLoading ? 'Indexando...' : 'Iniciar Indexação'}
        </Button>
      </CardFooter>
    </Card>
  );
} 