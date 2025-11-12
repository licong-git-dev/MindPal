/**
 * MindPal 数据埋点SDK
 * 自动追踪用户行为和关键事件
 */

const MindPalAnalytics = {
  // 配置
  config: {
    enabled: true,
    batchSize: 10,
    flushInterval: 5000, // 5秒
    sessionKey: 'mindpal_session_id'
  },

  // 会话ID
  sessionId: null,

  // 事件队列
  eventQueue: [],

  // 定时器
  flushTimer: null,

  /**
   * 初始化
   */
  init() {
    // 获取或创建会话ID
    this.sessionId = sessionStorage.getItem(this.config.sessionKey);
    if (!this.sessionId) {
      this.sessionId = this.generateUUID();
      sessionStorage.setItem(this.config.sessionKey, this.sessionId);
    }

    // 启动定时刷新
    this.startFlushTimer();

    // 页面卸载时发送剩余事件
    window.addEventListener('beforeunload', () => {
      this.flush(true);
    });

    // 自动追踪页面浏览
    this.trackPageView();

    console.log('[Analytics] SDK initialized, session:', this.sessionId);
  },

  /**
   * 生成UUID
   */
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  },

  /**
   * 获取当前用户ID
   */
  getUserId() {
    try {
      const user = MindPalAuth.getUser();
      return user ? user.id : null;
    } catch (e) {
      return null;
    }
  },

  /**
   * 追踪事件
   */
  track(eventName, metadata = {}) {
    if (!this.config.enabled) return;

    const event = {
      eventName,
      userId: this.getUserId(),
      sessionId: this.sessionId,
      metadata: {
        ...metadata,
        timestamp: new Date().toISOString(),
        page: window.location.pathname,
        url: window.location.href
      }
    };

    this.eventQueue.push(event);

    // 如果队列已满，立即发送
    if (this.eventQueue.length >= this.config.batchSize) {
      this.flush();
    }
  },

  /**
   * 追踪页面浏览
   */
  trackPageView() {
    const page = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
    this.track('page_view', {
      page,
      title: document.title,
      referrer: document.referrer
    });
  },

  /**
   * 追踪用户注册
   */
  trackRegister(userId) {
    this.track('user_register', {
      userId,
      method: 'phone'
    });
  },

  /**
   * 追踪用户登录
   */
  trackLogin(userId) {
    this.track('user_login', {
      userId,
      method: 'phone'
    });
  },

  /**
   * 追踪创建数字人
   */
  trackDHCreate(dhId, dhName) {
    this.track('dh_create', {
      dhId,
      dhName
    });
  },

  /**
   * 追踪发送消息
   */
  trackChatSend(dhId, messageLength) {
    this.track('chat_send', {
      dhId,
      messageLength
    });
  },

  /**
   * 追踪上传知识库
   */
  trackKBUpload(dhId, fileName, fileSize) {
    this.track('kb_upload', {
      dhId,
      fileName,
      fileSize
    });
  },

  /**
   * 追踪查看套餐
   */
  trackSubscriptionView() {
    this.track('subscription_view', {
      page: 'pricing'
    });
  },

  /**
   * 追踪点击付费
   */
  trackPaymentClick(planType, price) {
    this.track('payment_click', {
      planType,
      price
    });
  },

  /**
   * 追踪付费成功
   */
  trackPaymentSuccess(planType, price, paymentId) {
    this.track('payment_success', {
      planType,
      price,
      paymentId
    });
  },

  /**
   * 追踪按钮点击
   */
  trackButtonClick(buttonName, location) {
    this.track('button_click', {
      buttonName,
      location
    });
  },

  /**
   * 追踪错误
   */
  trackError(errorType, errorMessage, context = {}) {
    this.track('error', {
      errorType,
      errorMessage,
      ...context
    });
  },

  /**
   * 刷新事件队列
   */
  async flush(sync = false) {
    if (this.eventQueue.length === 0) return;

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      if (sync) {
        // 同步发送（页面卸载时使用）
        const data = JSON.stringify({ events });
        if (navigator.sendBeacon) {
          navigator.sendBeacon(
            `${MindPalConfig.API_BASE_URL}/api/analytics/batch`,
            new Blob([data], { type: 'application/json' })
          );
        }
      } else {
        // 异步发送
        const response = await fetch(`${MindPalConfig.API_BASE_URL}/api/analytics/batch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ events })
        });

        if (!response.ok) {
          console.error('[Analytics] Failed to send events:', response.status);
        }
      }
    } catch (error) {
      console.error('[Analytics] Error sending events:', error);
      // 发送失败，重新加入队列（可选）
      // this.eventQueue.unshift(...events);
    }
  },

  /**
   * 启动定时刷新
   */
  startFlushTimer() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  },

  /**
   * 停止定时刷新
   */
  stopFlushTimer() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  },

  /**
   * 启用埋点
   */
  enable() {
    this.config.enabled = true;
  },

  /**
   * 禁用埋点
   */
  disable() {
    this.config.enabled = false;
  }
};

// 自动初始化
if (typeof MindPalConfig !== 'undefined') {
  MindPalAnalytics.init();
}

// 导出到全局
window.MindPalAnalytics = MindPalAnalytics;
