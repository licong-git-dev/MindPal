/**
 * MindPal API配置
 */

const MindPalConfig = {
  // API Base URL
  API_BASE_URL: 'http://localhost:5000',

  // API Endpoints
  API: {
    // 认证相关
    AUTH: {
      REGISTER: '/api/auth/register',
      LOGIN: '/api/auth/login',
      VERIFY: '/api/auth/verify'
    },

    // 数字人相关
    DIGITAL_HUMANS: {
      LIST: '/api/digital-humans',
      CREATE: '/api/digital-humans',
      GET: (id) => `/api/digital-humans/${id}`,
      DELETE: (id) => `/api/digital-humans/${id}`
    },

    // 对话相关
    CHAT: {
      SEND: '/api/chat',
      HISTORY: (dhId) => `/api/chat/history/${dhId}`,
      CLEAR: (dhId) => `/api/chat/history/${dhId}`
    },

    // 知识库相关
    KNOWLEDGE: {
      UPLOAD: '/api/knowledge/upload',
      LIST: (dhId) => `/api/knowledge/${dhId}`,
      DELETE: (docId) => `/api/knowledge/${docId}`
    }
  },

  // 超时设置
  TIMEOUT: {
    DEFAULT: 30000,  // 30秒
    CHAT: 60000      // 对话60秒
  },

  // 重试设置
  RETRY: {
    MAX_ATTEMPTS: 3,
    DELAY: 1000
  }
};

// 导出到全局
window.MindPalConfig = MindPalConfig;
