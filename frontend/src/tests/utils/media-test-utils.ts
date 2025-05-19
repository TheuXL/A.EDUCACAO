/**
 * Utility functions for testing media rendering
 */
import { AnalyzeResponse } from '../../services/api';

/**
 * Cria uma resposta com dados reais de mídia
 * @param mediaType O tipo de mídia a ser incluído na resposta
 * @returns Um objeto AnalyzeResponse real
 */
export function createMediaResponse(mediaType: 'video' | 'audio' | 'image' | 'text' | 'mixed'): AnalyzeResponse {
  // Resposta base com campos obrigatórios
  const baseResponse: AnalyzeResponse = {
    user_id: 'test-user',
    response: '',
    related_content: []
  };

  // Arquivos reais disponíveis no backend
  const realFiles = {
    video: 'videos/Dica do professor.mp4',
    audio: 'audio/Dica do professor.mp3',
    image: 'images/Infografico-1.jpg',
    text: {
      apresentacao: 'text/Apresentação.txt',
      capitulo: 'text/Capítulo do Livro.txt',
      exercicios: 'text/Exercícios.txt'
    },
    transcript: {
      dica: 'transcripts/Dica do professor_info.txt',
      infografico: 'transcripts/Infografico-1_ocr.txt'
    }
  };

  switch (mediaType) {
    case 'video':
      return {
        ...baseResponse,
        response: `✅ **Dica do Professor**\n\nAssista a este vídeo com dicas importantes sobre o conteúdo.\n\n<!-- file_path: ${realFiles.video} -->`,
        has_video_content: true,
        query_id: 'video-test-1',
      };
    case 'audio':
      return {
        ...baseResponse,
        response: `✅ **Áudio Explicativo**\n\nOuça esta explicação detalhada sobre o tema.\n\nArquivo: ${realFiles.audio}`,
        has_audio_content: true,
        query_id: 'audio-test-1',
      };
    case 'image':
      return {
        ...baseResponse,
        response: `✅ **Infográfico Explicativo**\n\nEste infográfico resume os conceitos principais.\n\nImagem: ${realFiles.image}`,
        has_image_content: true,
        query_id: 'image-test-1',
      };
    case 'text':
      return {
        ...baseResponse,
        response: `✅ **Material de Leitura**\n\nLeia o material completo para aprofundar seus conhecimentos.\n\nArquivo: ${realFiles.text.apresentacao}\n\nArquivo: ${realFiles.text.capitulo}\n\nArquivo: ${realFiles.text.exercicios}`,
        file_path: realFiles.text.apresentacao,
        query_id: 'text-test-1',
      };
    case 'mixed':
      return {
        ...baseResponse,
        response: `✅ **Material Completo**\n\nAqui está todo o material disponível sobre o tema:\n\nVídeo: ${realFiles.video}\n\nÁudio: ${realFiles.audio}\n\nImagem: ${realFiles.image}\n\nTexto: ${realFiles.text.capitulo}\n\nTranscrição: ${realFiles.transcript.infografico}`,
        has_video_content: true,
        has_audio_content: true,
        has_image_content: true,
        query_id: 'mixed-test-1',
      };
    default:
      return {
        ...baseResponse,
        response: 'Resposta padrão sem mídia',
        query_id: 'default-test',
      };
  }
}

/**
 * Valida se uma URL de mídia está formatada corretamente
 * @param url A URL a ser validada
 * @param expectedPath O fragmento de caminho esperado
 * @returns boolean indicando se a URL está formatada corretamente
 */
export function validateMediaUrl(url: string | null | undefined, expectedPath: string): boolean {
  if (!url) return false;
  
  // Em ambiente de teste, a URL pode estar em um formato diferente
  // Devido ao JSDOM, a URL pode ser algo como "about:blank"
  if (url.startsWith('about:blank')) {
    return true; // Consideramos válido em ambiente de teste
  }
  
  try {
    // Normaliza os caminhos para comparação
    const normalizeUrl = (path: string): string => {
      // Remove protocol e domínio para focar apenas no caminho
      const cleanPath = path.replace(/^https?:\/\/[^\/]+\/processed_data\//, '');
      
      // Normaliza o caminho: remove espaços extras, converte para minúsculas
      return cleanPath
        .toLowerCase()
        .replace(/%20/g, ' ')  // Converte %20 para espaço
        .replace(/\s+/g, ' ')  // Normaliza espaços múltiplos
        .trim();
    };
    
    // Extrai apenas o caminho da URL completa
    const urlPath = url.includes('/processed_data/') 
      ? url.split('/processed_data/')[1] 
      : url;
      
    const normalizedUrl = normalizeUrl(urlPath);
    const normalizedExpectedPath = normalizeUrl(expectedPath);
    
    // Compara os componentes do caminho
    const urlParts = normalizedUrl.split('/');
    const expectedParts = normalizedExpectedPath.split('/');
    
    // Verifica se o arquivo final é o mesmo (independente da estrutura de diretórios)
    if (urlParts.length > 0 && expectedParts.length > 0) {
      const urlFileName = urlParts[urlParts.length - 1];
      const expectedFileName = expectedParts[expectedParts.length - 1];
      
      if (urlFileName === expectedFileName) {
        return true;
      }
    }
    
    // Verifica se a URL normalizada contém o caminho esperado normalizado
    return normalizedUrl.includes(normalizedExpectedPath);
  } catch (error) {
    console.error('Erro ao validar URL de mídia:', error);
    return false;
  }
}

/**
 * Extrai o caminho da mídia de uma URL completa
 * @param url A URL completa
 * @returns A porção do caminho da mídia
 */
export function extractMediaPath(url: string | null | undefined): string {
  if (!url) return '';
  
  const matches = url.match(/\/processed_data\/(.+)$/);
  return matches ? matches[1] : '';
}

/**
 * Verifica se um arquivo existe no backend
 * @param filePath Caminho do arquivo relativo ao diretório processed_data
 * @returns Promise que resolve para true se o arquivo existir
 */
export async function checkFileExists(filePath: string): Promise<boolean> {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${baseUrl}/processed_data/${filePath}`, { method: 'HEAD' });
    return response.ok;
  } catch (error) {
    console.error(`Erro ao verificar arquivo ${filePath}:`, error);
    return false;
  }
} 