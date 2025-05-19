/**
 * Função para validar e formatar URLs de mídia
 * 
 * @param url URL ou caminho do arquivo de mídia
 * @returns URL formatada corretamente
 */
export const validateMediaUrl = (url: string = ''): string => {
  if (!url) return '';
  
  // Se já for uma URL completa, retorna como está
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  
  // Obtém a URL base da API
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  // Remove barras duplicadas e ajusta o caminho
  let cleanPath = url;
  
  // Se o caminho já começar com /processed_data, apenas adiciona a URL base
  if (cleanPath.startsWith('/processed_data/')) {
    return `${apiUrl}${cleanPath}`;
  }
  
  // Se o caminho começar com /home/ ou outro caminho absoluto, extrai apenas a parte após /processed_data/
  if (cleanPath.includes('/processed_data/')) {
    cleanPath = cleanPath.split('/processed_data/')[1];
  }
  
  // Remove barras iniciais extras se houver
  cleanPath = cleanPath.replace(/^\/+/, '');
  
  // Verifica se o caminho já contém uma pasta específica (text, audio, video, images)
  const mediaDirs = ['text/', 'audio/', 'videos/', 'images/', 'transcripts/'];
  const hasMediaDir = mediaDirs.some(dir => cleanPath.startsWith(dir));
  
  // Se não tiver um diretório específico, tenta inferir com base na extensão
  if (!hasMediaDir) {
    const extension = cleanPath.toLowerCase().split('.').pop() || '';
    
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(extension)) {
      cleanPath = `videos/${cleanPath}`;
    } else if (['mp3', 'wav', 'ogg', 'aac', 'm4a'].includes(extension)) {
      cleanPath = `audio/${cleanPath}`;
    } else if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension)) {
      cleanPath = `images/${cleanPath}`;
    } else if (['txt', 'md', 'pdf'].includes(extension)) {
      // Se contém "exercícios" no nome, coloca na pasta text
      if (cleanPath.toLowerCase().includes('exercício') || 
          cleanPath.toLowerCase().includes('exercicio') || 
          cleanPath.toLowerCase().includes('exercise')) {
        cleanPath = `text/${cleanPath}`;
      } else {
        cleanPath = `text/${cleanPath}`;
      }
    }
  }
  
  // Retorna a URL completa
  return `${apiUrl}/processed_data/${cleanPath}`;
};

/**
 * Determina o tipo de arquivo com base na extensão ou caminho
 * 
 * @param filePath Caminho do arquivo
 * @returns Tipo do arquivo: 'video', 'audio', 'image', 'markdown', 'exercises' ou 'unknown'
 */
export const getFileType = (filePath: string): 'video' | 'audio' | 'image' | 'markdown' | 'exercises' | 'unknown' => {
  if (!filePath) return 'unknown';
  
  const extension = filePath.toLowerCase().split('.').pop() || '';
  const path = filePath.toLowerCase();
  
  if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(extension) || path.includes('/videos/')) {
    return 'video';
  } else if (['mp3', 'wav', 'ogg', 'aac', 'm4a'].includes(extension) || path.includes('/audio/')) {
    return 'audio';
  } else if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension) || path.includes('/images/')) {
    return 'image';
  } else if (['json'].includes(extension) || path.includes('exercícios') || path.includes('exercicios')) {
    return 'exercises';
  } else if (['md', 'txt', 'pdf'].includes(extension) || path.includes('/text/')) {
    return 'markdown';
  }
  
  return 'unknown';
}; 