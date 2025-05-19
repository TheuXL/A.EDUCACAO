'use client';

import React from 'react';
import { FileUploader } from '@/components/admin/FileUploader';

export default function ContentManagementPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Gerenciamento de Conteúdo</h1>
        <p className="text-gray-600">
          Faça upload e gerencie os conteúdos indexados pelo sistema A.Educação.
        </p>
      </div>
      
      <div className="grid grid-cols-1 gap-6">
        <FileUploader />
        
        <div className="p-6 bg-gray-50 rounded-lg">
          <h2 className="text-lg font-medium mb-4">Sobre Indexação de Conteúdo</h2>
          <div className="space-y-4 text-sm text-gray-600">
            <p>
              A indexação de conteúdo permite que o sistema A.Educação processe e organize documentos, 
              vídeos e outros materiais para torná-los pesquisáveis e utilizáveis nas respostas adaptativas.
            </p>
            
            <div>
              <h3 className="font-medium text-gray-700 mb-2">Tipos de Arquivo Suportados</h3>
              <ul className="list-disc list-inside space-y-1 pl-2">
                <li><strong>Documentos:</strong> PDF, TXT, DOC, DOCX, MD</li>
                <li><strong>Imagens:</strong> JPG, JPEG, PNG, GIF</li>
                <li><strong>Vídeos:</strong> MP4, AVI, MOV</li>
                <li><strong>Exercícios:</strong> JSON (formato estruturado específico)</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-700 mb-2">Processamento de Conteúdo</h3>
              <p>
                Ao fazer upload, os arquivos são processados da seguinte forma:
              </p>
              <ul className="list-disc list-inside space-y-1 pl-2">
                <li>Textos são extraídos e analisados semanticamente</li>
                <li>Imagens são processadas para extração de metadados e conteúdo visual</li>
                <li>Vídeos têm seus metadados extraídos e podem ter transcrições geradas automaticamente</li>
                <li>Documentos estruturados são integrados ao sistema de aprendizagem adaptativa</li>
              </ul>
            </div>
            
            <div className="bg-blue-50 p-3 rounded-md border border-blue-100">
              <p className="text-blue-800">
                <strong>Dica:</strong> Para obter melhores resultados na indexação, certifique-se de que seus arquivos 
                estejam bem estruturados e contenham metadados relevantes, como títulos, autores e descrições.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 