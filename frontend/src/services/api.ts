import axios from 'axios';

// Definindo a URL base da API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Criando uma instância do Axios com configurações padrão
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interface para a solicitação de análise
export interface AnalyzeRequest {
  query: string;
  user_level?: string;
  preferred_format?: string;
  user_id?: string;
  use_neural_network?: boolean;
}

// Interface para as respostas do backend
export interface AnalyzeResponse {
  response: string;
  user_id: string;
  query_id?: string;
  related_content?: RelatedContent[];
  neural_enhanced?: boolean;
  has_video_content?: boolean;
  has_image_content?: boolean;
  has_audio_content?: boolean;
  user_level?: string;
  preferred_format?: string;
  file_path?: string;
  primary_media_type?: 'video' | 'audio' | 'image' | 'text' | 'exercises' | 'mixed';
}

// Interface para o conteúdo relacionado
export interface RelatedContent {
  id: string;
  title: string;
  type: string;
  content_preview?: string;
  preview?: string;
  source?: string;
}

// Interface para os resultados de busca
export interface SearchResult {
  id: string;
  type: string;
  content_preview: string;
  preview?: string;
  metadata: {
    source?: string;
    title?: string;
    size_bytes?: number;
    pages?: number;
    duration_seconds?: number;
  };
}

// Interface para a resposta de busca
export interface SearchResponse {
  success: boolean;
  query: string;
  count: number;
  results: SearchResult[];
  neural_enhanced: boolean;
}

// Interface para a análise de lacunas de aprendizagem
export interface GapAnalysisResponse {
  user_id: string;
  status: string;
  analysis_date?: string;
  overall_progress?: number;
  engagement_metrics?: Record<string, any>;
  identified_gaps: Array<{
    topic: string;
    severity: string;
    confidence: number;
    suggestions?: string[];
  }>;
  improvement_suggestions?: Array<{
    resource_type: string;
    title: string;
    description: string;
    difficulty: string;
  }>;
  strengths: string[];
  weaknesses: string[];
  message?: string;
}

// Interface para o plano de melhoria
export interface ImprovementPlanResponse {
  user_id: string;
  status: string;
  creation_date?: string;
  recommended_completion_date?: string;
  plan_title?: string;
  steps: Array<{
    id: string;
    title: string;
    description: string;
    resource_type: string;
    estimated_time: string;
    difficulty: string;
  }>;
  overall_goal?: string;
  message?: string;
}

// Interface para atualização de perfil
export interface ProfileUpdateRequest {
  user_id: string;
  level?: string;
  preferred_format?: string;
  interests?: string[];
  update_strengths_weaknesses?: boolean;
}

// Funções para comunicação com o backend

// Processa a resposta da API garantindo que o formato seja consistente
function processApiResponse(data: any): AnalyzeResponse {
  // Se a resposta já estiver formatada corretamente
  if (data && typeof data.response === 'string') {
    // Extrai o caminho do arquivo da resposta, se existir
    const filePathMatch = data.response.match(/<!-- file_path: (.*?) -->/);
    if (filePathMatch) {
      data.file_path = filePathMatch[1];
    }
    return data as AnalyzeResponse;
  }
  
  // Se a resposta for uma string JSON, tenta parseá-la
  if (typeof data === 'string') {
    try {
      const parsedData = JSON.parse(data);
      if (parsedData && typeof parsedData.response === 'string') {
        // Extrai o caminho do arquivo da resposta, se existir
        const filePathMatch = parsedData.response.match(/<!-- file_path: (.*?) -->/);
        if (filePathMatch) {
          parsedData.file_path = filePathMatch[1];
        }
        return parsedData as AnalyzeResponse;
      }
      // Se a resposta parseada não tiver o formato esperado
      return {
        response: typeof parsedData === 'string' ? parsedData : JSON.stringify(parsedData),
        user_id: 'unknown'
      };
    } catch (e) {
      // Se não for um JSON válido, assume que é a resposta em texto
      const response = data;
      // Extrai o caminho do arquivo da resposta, se existir
      const filePathMatch = response.match(/<!-- file_path: (.*?) -->/);
      return {
        response,
        user_id: 'unknown',
        file_path: filePathMatch ? filePathMatch[1] : undefined
      };
    }
  }
  
  // Se a resposta não tiver o formato esperado
  return {
    response: typeof data === 'object' ? JSON.stringify(data) : String(data),
    user_id: 'unknown'
  };
}

/**
 * Envia uma consulta para análise e obtenção de conteúdos adaptados
 */
export const analyzeQuery = async (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
  try {
    const response = await api.post<AnalyzeResponse>('/api/analyze', data);
    return processApiResponse(response.data);
  } catch (error) {
    console.error('Erro ao analisar consulta:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao analisar consulta');
    }
    throw error;
  }
};

/**
 * Busca conteúdos com base em uma consulta
 */
export const searchContent = async (
  query: string, 
  limit: number = 5, 
  docType?: string
): Promise<SearchResponse> => {
  try {
    const params: Record<string, string | number> = {
      q: query,
      limit
    };
    
    if (docType) {
      params.doc_type = docType;
    }
    
    const response = await api.get<SearchResponse>('/api/search', { params });
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar conteúdos:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao buscar conteúdos');
    }
    throw error;
  }
};

/**
 * Envia feedback sobre uma resposta
 */
export const sendFeedback = async (userId: string, queryId: string, feedback: string): Promise<{ success: boolean }> => {
  try {
    const response = await api.post('/api/feedback', {
      user_id: userId,
      query_id: queryId,
      feedback
    });
    return response.data;
  } catch (error) {
    console.error('Erro ao enviar feedback:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao enviar feedback');
    }
    throw error;
  }
};

/**
 * Analisa lacunas de aprendizado de um usuário
 */
export const analyzeLearningGaps = async (userId: string): Promise<GapAnalysisResponse> => {
  try {
    const response = await api.get<GapAnalysisResponse>(`/api/learning/analysis/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao analisar lacunas de aprendizado:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao analisar lacunas de aprendizado');
    }
    throw error;
  }
};

/**
 * Gera um plano de melhoria para o usuário
 */
export const generateImprovementPlan = async (userId: string): Promise<ImprovementPlanResponse> => {
  try {
    const response = await api.get<ImprovementPlanResponse>(`/api/learning/improvement-plan/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao gerar plano de melhoria:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao gerar plano de melhoria');
    }
    throw error;
  }
};

/**
 * Atualiza o perfil do usuário, incluindo pontos fortes e fracos
 */
export const updateUserProfile = async (data: ProfileUpdateRequest): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.post('/api/learning/update-profile', data);
    return response.data;
  } catch (error) {
    console.error('Erro ao atualizar perfil do usuário:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao atualizar perfil do usuário');
    }
    throw error;
  }
};

/**
 * Faz upload de arquivos para indexação
 */
export const uploadFiles = async (files: File[]): Promise<{ success: boolean; uploaded_files: string[] }> => {
  try {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post('/api/index', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('Erro ao fazer upload de arquivos:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao fazer upload de arquivos');
    }
    throw error;
  }
};

/**
 * Executa testes de performance do sistema
 */
export const runPerformanceTest = async (
  testDir: string = '/tmp/aeducacao_test',
  apiUrl?: string,
  testType: string = 'all'
): Promise<any> => {
  try {
    const response = await api.post('/api/admin/performance-test', {
      test_dir: testDir,
      api_url: apiUrl,
      test_type: testType
    });
    
    return response.data;
  } catch (error) {
    console.error('Erro ao executar teste de performance:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao executar teste de performance');
    }
    throw error;
  }
};

/**
 * Gera exercícios com base nas lacunas de conhecimento identificadas
 */
export const generateExercises = async (
  topic: string,
  level: string = 'intermediário',
  format: string = 'texto'
): Promise<AnalyzeResponse> => {
  try {
    const response = await api.post<AnalyzeResponse>('/api/analyze', {
      query: `Gere um exercício sobre ${topic} para nível ${level}`,
      user_level: level,
      preferred_format: format,
      use_neural_network: true
    });
    return processApiResponse(response.data);
  } catch (error) {
    console.error('Erro ao gerar exercícios:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Erro ao gerar exercícios');
    }
    throw error;
  }
};

export default api; 