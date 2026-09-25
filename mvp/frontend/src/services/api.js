import axios from 'axios'

const API_BASE = '/api'

// Dataset API
export const datasetApi = {
  upload: async (file, name) => {
    const formData = new FormData()
    formData.append('file', file)
    if (name) formData.append('name', name)
    
    const response = await axios.post(`${API_BASE}/datasets/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  list: async () => {
    const response = await axios.get(`${API_BASE}/datasets`)
    return response.data.datasets
  },
  
  get: async (datasetId) => {
    const response = await axios.get(`${API_BASE}/datasets/${datasetId}`)
    return response.data
  },
  
  getProfile: async (datasetId) => {
    const response = await axios.get(`${API_BASE}/datasets/${datasetId}/profile`)
    return response.data
  },
  
  validate: async (datasetId, targetColumn = null) => {
    const response = await axios.post(
      `${API_BASE}/datasets/${datasetId}/validate`,
      null,
      { params: { target_column: targetColumn } }
    )
    return response.data
  }
}

// Experiment API
export const experimentApi = {
  create: async (datasetId, config = {}) => {
    const response = await axios.post(`${API_BASE}/experiments`, {
      dataset_id: datasetId,
      ...config
    })
    return response.data
  },
  
  list: async (filters = {}) => {
    const response = await axios.get(`${API_BASE}/experiments`, { params: filters })
    return response.data.experiments
  },
  
  get: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}`)
    return response.data
  },
  
  run: async (experimentId) => {
    const response = await axios.post(`${API_BASE}/experiments/${experimentId}/run`)
    return response.data
  },
  
  getStatus: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}/status`)
    return response.data
  },
  
  getResults: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}/results`)
    return response.data.results
  },
  
  getMetrics: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}/metrics`)
    return response.data.metrics
  },
  
  getComparison: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}/comparison`)
    return response.data
  },
  
  getResources: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}/resources`)
    return response.data
  },
  
  getRecommendation: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/experiments/${experimentId}/recommendation`)
    return response.data
  }
}

// Report API
export const reportApi = {
  generate: async (experimentId) => {
    const response = await axios.post(`${API_BASE}/reports/${experimentId}`)
    return response.data
  },
  
  get: async (experimentId) => {
    const response = await axios.get(`${API_BASE}/reports/${experimentId}`)
    return response.data
  },
  
  download: async (experimentId) => {
    window.open(`${API_BASE}/reports/${experimentId}/download`, '_blank')
  }
}

export default { datasetApi, experimentApi, reportApi }
