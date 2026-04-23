/**
 * MindPal API封装层
 * 提供统一的API调用接口
 */

const MindPalAPI = {
  /**
   * 通用请求方法
   */
  async request(url, options = {}) {
    const defaultOptions = {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    // 添加认证token
    const token = MindPalAuth.getAuthToken();
    if (token && !token.startsWith('temp_')) {
      defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }

    const finalOptions = { ...defaultOptions, ...options };

    // 合并headers
    if (options.headers) {
      finalOptions.headers = { ...defaultOptions.headers, ...options.headers };
    }

    try {
      const response = await fetch(`${MindPalConfig.API_BASE_URL}${url}`, finalOptions);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP Error: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  },

  /**
   * 认证API
   */
  auth: {
    /**
     * 用户注册
     */
    async register(username, email, password) {
      const response = await fetch(`${MindPalConfig.API_BASE_URL}${MindPalConfig.API.AUTH.REGISTER}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || '注册失败');
      }

      if (result.code !== 0) {
        throw new Error(result.message || '注册失败');
      }

      // 保存登录信息
      const data = result.data;
      MindPalAuth.saveLogin({
        id: data.user_id,
        username: data.username
      }, data.access_token);

      return result;
    },

    /**
     * 用户登录
     */
    async login(account, password) {
      const response = await fetch(`${MindPalConfig.API_BASE_URL}${MindPalConfig.API.AUTH.LOGIN}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account, password })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || '登录失败');
      }

      if (result.code !== 0) {
        throw new Error(result.message || '登录失败');
      }

      // 保存登录信息
      const data = result.data;
      MindPalAuth.saveLogin({
        id: data.user_id,
        username: data.username,
        player_id: data.player_id,
        has_character: data.has_character
      }, data.access_token);

      return result;
    },

    /**
     * 刷新Token
     */
    async refresh() {
      const response = await fetch(`${MindPalConfig.API_BASE_URL}${MindPalConfig.API.AUTH.REFRESH}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      const result = await response.json();

      if (!response.ok || result.code !== 0) {
        MindPalAuth.logout();
        throw new Error('Token refresh failed');
      }

      // 更新access_token
      sessionStorage.setItem('mindpal_token', result.data.access_token);

      return result;
    },

    /**
     * 获取当前用户信息
     */
    async me() {
      return await MindPalAPI.request(MindPalConfig.API.AUTH.VERIFY);
    }
  },

  /**
   * 数字人API
   */
  digitalHumans: {
    /**
     * 获取数字人列表
     */
    async list() {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.LIST);
    },

    /**
     * 创建数字人
     */
    async create(dhData) {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.CREATE, {
        method: 'POST',
        body: JSON.stringify(dhData)
      });
    },

    /**
     * 获取数字人详情
     */
    async get(dhId) {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.GET(dhId));
    },

    /**
     * 更新数字人
     */
    async update(dhId, dhData) {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.UPDATE(dhId), {
        method: 'PUT',
        body: JSON.stringify(dhData)
      });
    },

    /**
     * 删除数字人
     */
    async delete(dhId) {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.DELETE(dhId), {
        method: 'DELETE'
      });
    },

    /**
     * 与数字人对话 (流式SSE)
     */
    async chat(dhId, message, sessionId, onChunk, onComplete, onError) {
      const token = MindPalAuth.getAuthToken();

      try {
        const response = await fetch(
          `${MindPalConfig.API_BASE_URL}${MindPalConfig.API.DIGITAL_HUMANS.CHAT_STREAM(dhId)}`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': token && !token.startsWith('temp_') ? `Bearer ${token}` : ''
            },
            body: JSON.stringify({
              dh_id: dhId,
              message: message,
              session_id: sessionId || null
            })
          }
        );

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || `HTTP Error: ${response.status}`);
        }

        // 处理SSE流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === 'chunk' && data.content) {
                  fullResponse += data.content;
                  onChunk && onChunk(data.content, fullResponse);
                } else if (data.type === 'done') {
                  onComplete && onComplete({
                    response: fullResponse,
                    session_id: data.session_id,
                    tokens_used: data.tokens_used
                  });
                  return;
                } else if (data.type === 'error') {
                  onError && onError(data.message);
                  return;
                }
              } catch (e) {
                console.error('解析SSE消息失败:', e, line);
              }
            }
          }
        }

        // 流结束但没有收到done信号
        if (fullResponse) {
          onComplete && onComplete({ response: fullResponse });
        }

      } catch (error) {
        console.error('数字人对话失败:', error);
        onError && onError(error.message);
      }
    },

    /**
     * 获取对话历史
     */
    async getHistory(dhId, limit = 50) {
      return await MindPalAPI.request(
        `${MindPalConfig.API.DIGITAL_HUMANS.HISTORY(dhId)}?limit=${limit}`
      );
    },

    /**
     * 获取性格选项列表
     */
    async getPersonalities() {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.PERSONALITIES);
    },

    /**
     * 获取领域选项列表
     */
    async getDomains() {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.DOMAINS);
    }
  },

  /**
   * 对话API
   */
  chat: {
    /**
     * 发送消息 (流式SSE)
     */
    async sendMessage(dhId, message, onChunk, onComplete, onError) {
      const token = MindPalAuth.getAuthToken();

      try {
        const response = await fetch(`${MindPalConfig.API_BASE_URL}${MindPalConfig.API.CHAT.SEND}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token && !token.startsWith('temp_') ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({ dhId, message })
        });

        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status}`);
        }

        // 处理SSE流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // 处理完整的SSE消息
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // 保留不完整的行

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.chunk) {
                  onChunk && onChunk(data.chunk);
                } else if (data.done) {
                  onComplete && onComplete(data);
                  return;
                } else if (data.error) {
                  onError && onError(data.error);
                  return;
                }
              } catch (e) {
                console.error('解析SSE消息失败:', e);
              }
            }
          }
        }

      } catch (error) {
        console.error('发送消息失败:', error);
        onError && onError(error.message);
      }
    },

    /**
     * 获取对话历史
     */
    async getHistory(dhId, limit = 50, offset = 0) {
      return await MindPalAPI.request(
        `${MindPalConfig.API.CHAT.HISTORY(dhId)}?limit=${limit}&offset=${offset}`
      );
    },

    /**
     * 清空对话历史
     */
    async clearHistory(dhId) {
      return await MindPalAPI.request(MindPalConfig.API.CHAT.CLEAR(dhId), {
        method: 'DELETE'
      });
    }
  },

  /**
   * 知识库API (预留)
   */
  knowledge: {
    async upload(dhId, file) {
      const formData = new FormData();
      formData.append('dhId', dhId);
      formData.append('file', file);

      return await MindPalAPI.request(MindPalConfig.API.KNOWLEDGE.UPLOAD, {
        method: 'POST',
        headers: {}, // 让浏览器自动设置Content-Type为multipart/form-data
        body: formData
      });
    },

    async list(dhId) {
      return await MindPalAPI.request(MindPalConfig.API.KNOWLEDGE.LIST(dhId));
    },

    async delete(docId) {
      return await MindPalAPI.request(MindPalConfig.API.KNOWLEDGE.DELETE(docId), {
        method: 'DELETE'
      });
    }
  },

  /**
   * 订阅系统API
   */
  subscription: {
    /**
     * 创建订阅
     */
    async create(planType, paymentId) {
      return await MindPalAPI.request(MindPalConfig.API.SUBSCRIPTION.CREATE, {
        method: 'POST',
        body: JSON.stringify({ planType, paymentId })
      });
    },

    /**
     * 获取订阅状态
     */
    async getStatus() {
      return await MindPalAPI.request(MindPalConfig.API.SUBSCRIPTION.STATUS);
    },

    /**
     * 取消订阅
     */
    async cancel() {
      return await MindPalAPI.request(MindPalConfig.API.SUBSCRIPTION.CANCEL, {
        method: 'POST'
      });
    },

    /**
     * 获取配额信息
     */
    async getQuota() {
      return await MindPalAPI.request(MindPalConfig.API.SUBSCRIPTION.QUOTA);
    },

    /**
     * 获取订阅历史
     */
    async getHistory() {
      return await MindPalAPI.request(MindPalConfig.API.SUBSCRIPTION.HISTORY);
    },

    /**
     * 升级预览
     */
    async upgradePreview(planType) {
      return await MindPalAPI.request(MindPalConfig.API.SUBSCRIPTION.UPGRADE_PREVIEW, {
        method: 'POST',
        body: JSON.stringify({ planType })
      });
    }
  },

  /**
   * 数据埋点API
   */
  analytics: {
    /**
     * 追踪事件
     */
    async track(eventName, metadata = {}) {
      return await MindPalAPI.request(MindPalConfig.API.ANALYTICS.TRACK, {
        method: 'POST',
        body: JSON.stringify({ eventName, metadata })
      });
    },

    /**
     * 批量追踪事件
     */
    async batch(events) {
      return await MindPalAPI.request(MindPalConfig.API.ANALYTICS.BATCH, {
        method: 'POST',
        body: JSON.stringify({ events })
      });
    },

    /**
     * 获取面板数据
     */
    async getDashboard(range = 7) {
      return await MindPalAPI.request(`${MindPalConfig.API.ANALYTICS.DASHBOARD}?range=${range}`);
    },

    /**
     * 获取事件列表
     */
    async getEvents(eventName, limit = 100, offset = 0) {
      let url = `${MindPalConfig.API.ANALYTICS.EVENTS}?limit=${limit}&offset=${offset}`;
      if (eventName) {
        url += `&event=${eventName}`;
      }
      return await MindPalAPI.request(url);
    },

    /**
     * 获取转化漏斗
     */
    async getFunnel(range = 30) {
      return await MindPalAPI.request(`${MindPalConfig.API.ANALYTICS.FUNNEL}?range=${range}`);
    }
  }
};

// 导出到全局
window.MindPalAPI = MindPalAPI;
