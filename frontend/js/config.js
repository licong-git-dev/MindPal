/**
 * MindPal API配置
 */

const runtimeApiBaseUrl = window.__MINDPAL_API_BASE_URL__ || '';

const MindPalConfig = {
  // API Base URL
  // 默认使用同源相对路径，避免部署后请求落到访问者本机 localhost。
  API_BASE_URL: runtimeApiBaseUrl,

  // API Endpoints
  API: {
    // 认证相关
    AUTH: {
      REGISTER: '/api/v1/auth/register',
      LOGIN: '/api/v1/auth/login',
      REFRESH: '/api/v1/auth/refresh',
      VERIFY: '/api/v1/auth/me'
    },

    // 数字人相关
    DIGITAL_HUMANS: {
      LIST: '/api/v1/digital-humans',
      CREATE: '/api/v1/digital-humans',
      GET: (id) => `/api/v1/digital-humans/${id}`,
      UPDATE: (id) => `/api/v1/digital-humans/${id}`,
      DELETE: (id) => `/api/v1/digital-humans/${id}`,
      CHAT: (id) => `/api/v1/digital-humans/${id}/chat`,
      CHAT_STREAM: (id) => `/api/v1/digital-humans/${id}/chat/stream`,
      HISTORY: (id) => `/api/v1/digital-humans/${id}/history`,
      PERSONALITIES: '/api/v1/digital-humans/options/personalities',
      DOMAINS: '/api/v1/digital-humans/options/domains'
    },

    // 对话相关 (旧NPC对话系统)
    CHAT: {
      SEND: '/api/v1/dialogue/chat',
      STREAM: '/api/v1/dialogue/stream',
      HISTORY: (npcId) => `/api/v1/dialogue/history?npc_id=${npcId}`,
      AFFINITY: '/api/v1/dialogue/affinity'
    },

    // 语音相关
    VOICE: {
      TTS: '/api/v1/voice/tts',
      TTS_NPC: '/api/v1/voice/tts/npc',
      ASR: '/api/v1/voice/asr',
      ASR_UPLOAD: '/api/v1/voice/asr/upload',
      VOICES: '/api/v1/voice/voices',
      NPC_VOICES: '/api/v1/voice/npc-voices'
    },

    // 知识库相关
    KNOWLEDGE: {
      UPLOAD: '/api/v1/knowledge/upload',
      LIST: (dhId) => `/api/v1/knowledge/${dhId}`,
      DELETE: (docId) => `/api/v1/knowledge/${docId}`
    },

    // 数字人长期记忆（可视化记忆时间线）
    MEMORIES: {
      LIST: (dhId) => `/api/v1/digital-humans/${dhId}/memories`,
      STATS: (dhId) => `/api/v1/digital-humans/${dhId}/memories/stats`,
      DELETE: (dhId, memoryId) => `/api/v1/digital-humans/${dhId}/memories/${encodeURIComponent(memoryId)}`,
      CLEAR: (dhId) => `/api/v1/digital-humans/${dhId}/memories?confirm=true`,
    },

    // 订阅相关
    SUBSCRIPTION: {
      CREATE: '/api/v1/subscription/create',
      STATUS: '/api/v1/subscription/status',
      CANCEL: '/api/v1/subscription/cancel',
      QUOTA: '/api/v1/subscription/quota',
      HISTORY: '/api/v1/subscription/history',
      UPGRADE_PREVIEW: '/api/v1/subscription/upgrade-preview'
    },

    // 支付相关
    PAYMENT: {
      PRODUCTS: '/api/v1/payment/products',
      CREATE_ORDER: '/api/v1/payment/orders',
      ORDER_LIST: '/api/v1/payment/orders',
      ORDER_DETAIL: (orderNo) => `/api/v1/payment/orders/${orderNo}`,
      CANCEL_ORDER: (orderNo) => `/api/v1/payment/orders/${orderNo}/cancel`,
      VIP_STATUS: '/api/v1/payment/vip/status',
      // 测试支付
      MOCK_CREATE: '/api/v1/payment/mock/create',
      MOCK_PAY: (orderNo) => `/api/v1/payment/mock/pay/${orderNo}`,
      TEST_ADD_DIAMONDS: '/api/v1/payment/test/add-diamonds',
      TEST_ADD_GOLD: '/api/v1/payment/test/add-gold'
    },

    // 数据埋点相关
    ANALYTICS: {
      TRACK: '/api/v1/analytics/track',
      BATCH: '/api/v1/analytics/batch',
      DASHBOARD: '/api/v1/analytics/dashboard',
      EVENTS: '/api/v1/analytics/events',
      FUNNEL: '/api/v1/analytics/funnel'
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
