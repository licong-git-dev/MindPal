/**
 * MindPal API封装层
 * 提供统一的API调用接口
 */

const MindPalAPI = {
  /**
   * SSE 流解析器 - 解析标准 Server-Sent Events 格式
   *
   * 每个事件由 `\n\n` 分隔，事件内部：
   *   event: <type>\n
   *   data: <json>\n
   *
   * 多行 data: 会被拼接，event 缺省时默认为 "message"。
   * handlers 支持: onStart, onDelta, onCrisis, onMeta, onDone, onError, onEvent
   *
   * @param {Response} response - fetch 返回的 Response
   * @param {Object} handlers
   */
  async _parseSSEStream(response, handlers) {
    const h = handlers || {};
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const dispatch = (type, data) => {
      switch (type) {
        case 'start':   h.onStart  && h.onStart(data);  break;
        case 'delta':   h.onDelta  && h.onDelta(data);  break;
        case 'crisis':  h.onCrisis && h.onCrisis(data); break;
        case 'meta':    h.onMeta   && h.onMeta(data);   break;
        case 'done':    h.onDone   && h.onDone(data);   break;
        case 'error':   h.onError  && h.onError(data);  break;
        default:        h.onEvent  && h.onEvent(type, data);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 按 \n\n 切分事件块
      let idx;
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);

        if (!block.trim()) continue;

        let eventType = 'message';
        const dataLines = [];

        for (const line of block.split('\n')) {
          if (line.startsWith('event:')) {
            eventType = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            dataLines.push(line.slice(5).trimStart());
          }
        }

        if (dataLines.length === 0) continue;

        const rawData = dataLines.join('\n');
        let parsed;
        try {
          parsed = JSON.parse(rawData);
        } catch (e) {
          parsed = { raw: rawData };
        }

        dispatch(eventType, parsed);

        // done/error 提前退出
        if (eventType === 'done' || eventType === 'error') {
          return;
        }
      }
    }

    // 处理可能残留的最后一块（没有 \n\n 收尾）
    if (buffer.trim()) {
      let eventType = 'message';
      const dataLines = [];
      for (const line of buffer.split('\n')) {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trimStart());
        }
      }
      if (dataLines.length) {
        const rawData = dataLines.join('\n');
        let parsed;
        try { parsed = JSON.parse(rawData); }
        catch (e) { parsed = { raw: rawData }; }
        dispatch(eventType, parsed);
      }
    }
  },

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
     *
     * 后端发送标准 SSE 格式（每个事件以 \n\n 分隔）:
     *   event: start     data: {session_id, dh_id, emotion, crisis_detected, model}
     *   event: crisis    data: {resources, level, hotline}  [仅危机模式]
     *   event: meta      data: {emotion, crisis_level, ...} [pipeline metadata]
     *   event: delta     data: {content}                    [增量文本]
     *   event: done      data: {full_response, emotion, memories_used, ...}
     *   event: error     data: {error, reason}
     *
     * @param {Object} callbacks - { onStart, onChunk, onMeta, onCrisis, onComplete, onError }
     */
    async chat(dhId, message, sessionId, callbacks) {
      const cbs = callbacks || {};
      // 向后兼容旧签名: chat(dhId, message, sessionId, onChunk, onComplete, onError)
      if (typeof callbacks === 'function') {
        cbs.onChunk = arguments[3];
        cbs.onComplete = arguments[4];
        cbs.onError = arguments[5];
      }

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
          let errMsg = `HTTP Error: ${response.status}`;
          try {
            const err = await response.json();
            errMsg = err.detail || err.message || errMsg;
          } catch (_) { /* body 不是 JSON，忽略 */ }
          throw new Error(errMsg);
        }

        let fullResponse = '';
        let startMeta = {};

        await MindPalAPI._parseSSEStream(response, {
          onStart: (data) => {
            startMeta = data || {};
            cbs.onStart && cbs.onStart(data);
            // start 帧本身携带 emotion/crisis_detected，也触发 meta 回调
            if (data && (data.emotion || data.crisis_detected !== undefined)) {
              cbs.onMeta && cbs.onMeta({
                emotion: data.emotion,
                crisis_detected: data.crisis_detected,
                model: data.model
              });
            }
          },
          onDelta: (data) => {
            if (data && typeof data.content === 'string') {
              fullResponse += data.content;
              cbs.onChunk && cbs.onChunk(data.content, fullResponse);
            }
          },
          onCrisis: (data) => {
            cbs.onCrisis && cbs.onCrisis(data || {});
          },
          onMeta: (data) => {
            cbs.onMeta && cbs.onMeta(data || {});
          },
          onDone: (data) => {
            const payload = data || {};
            cbs.onComplete && cbs.onComplete({
              response: fullResponse || payload.full_response || '',
              session_id: startMeta.session_id || payload.session_id,
              emotion: payload.emotion || startMeta.emotion,
              emotion_intensity: payload.emotion_intensity,
              crisis_detected: payload.crisis_detected || startMeta.crisis_detected,
              affinity_change: payload.affinity_change,
              memories_used: payload.memories_used,
              model_used: payload.model_used || startMeta.model,
              tokens_used: payload.tokens_used
            });
          },
          onError: (data) => {
            const msg = (data && (data.error || data.reason || data.message)) || 'Stream error';
            cbs.onError && cbs.onError(msg);
          }
        });

        // 流正常结束但后端没发 done（兜底）
        if (fullResponse && cbs.onComplete) {
          cbs.onComplete({ response: fullResponse, session_id: startMeta.session_id });
        }

      } catch (error) {
        console.error('数字人对话失败:', error);
        cbs.onError && cbs.onError(error.message || String(error));
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
     * 按大类分组的性格选项（返回 { categories: { companion: [...], romantic: [...] } }）
     */
    async getPersonalitiesGrouped() {
      return await MindPalAPI.request(MindPalConfig.API.DIGITAL_HUMANS.PERSONALITIES_GROUPED);
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

        let fullResponse = '';
        await MindPalAPI._parseSSEStream(response, {
          onDelta: (data) => {
            if (data && typeof data.content === 'string') {
              fullResponse += data.content;
              onChunk && onChunk(data.content);
            }
          },
          onDone: (data) => {
            onComplete && onComplete({ ...(data || {}), response: fullResponse || (data && data.full_response) || '' });
          },
          onError: (data) => {
            onError && onError((data && (data.error || data.reason || data.message)) || 'Stream error');
          }
        });

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
   * 语音 API（ASR 语音识别 + TTS 语音合成）
   *
   * 依赖后端 backend_v2/app/api/v1/voice.py:
   *   POST /voice/asr/upload  multipart 音频 → 识别文本
   *   POST /voice/tts         json { text, voice } → audio/mpeg blob
   */
  voice: {
    /**
     * 上传音频文件识别为文本
     * @param {Blob} audioBlob - 录音 blob
     * @param {string} format - wav / mp3 / pcm / webm（浏览器录音默认 webm）
     * @param {number} sampleRate - 采样率
     * @returns 识别结果 { code, data: { text, confidence, duration } }
     */
    async asrUpload(audioBlob, format = 'webm', sampleRate = 16000) {
      const token = MindPalAuth.getAuthToken();
      const fd = new FormData();
      fd.append('file', audioBlob, `record.${format}`);
      fd.append('format', format);
      fd.append('sample_rate', String(sampleRate));

      const response = await fetch(
        `${MindPalConfig.API_BASE_URL}${MindPalConfig.API.VOICE.ASR_UPLOAD}`,
        {
          method: 'POST',
          headers: {
            'Authorization': token && !token.startsWith('temp_') ? `Bearer ${token}` : '',
          },
          body: fd,
        }
      );
      if (!response.ok) {
        let msg = `HTTP ${response.status}`;
        try { const j = await response.json(); msg = j.detail || j.message || msg; } catch (_) {}
        throw new Error(msg);
      }
      return await response.json();
    },

    /**
     * 文本转语音
     * @param {string} text - 要合成的文本
     * @param {string} voice - 语音 id（见 /voice/voices）
     * @param {string} format - mp3 / wav / pcm
     * @returns Blob 音频
     */
    async ttsSynthesize(text, voice = 'xiaoyun', format = 'mp3') {
      const token = MindPalAuth.getAuthToken();
      const response = await fetch(
        `${MindPalConfig.API_BASE_URL}${MindPalConfig.API.VOICE.TTS}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token && !token.startsWith('temp_') ? `Bearer ${token}` : '',
          },
          body: JSON.stringify({ text, voice, format }),
        }
      );
      if (!response.ok) {
        let msg = `HTTP ${response.status}`;
        try { const j = await response.json(); msg = j.detail || j.message || msg; } catch (_) {}
        throw new Error(msg);
      }
      return await response.blob();
    },

    /** 获取可用语音列表 */
    async getVoices() {
      return await MindPalAPI.request(MindPalConfig.API.VOICE.VOICES);
    },
  },

  /**
   * 数字人长期记忆 API（可视化记忆时间线）
   *
   * 全部挂在 /api/v1/digital-humans/{dh_id}/memories/*，不依赖 Player 模型。
   */
  memories: {
    /**
     * 列出记忆
     * @param {number} dhId - 数字人 ID
     * @param {Object} opts - { limit, offset, emotion, q }
     *   q: 传入则走语义搜索；emotion: 按情感筛选；都不传则时间线
     */
    async list(dhId, opts = {}) {
      const params = new URLSearchParams();
      if (opts.limit != null) params.set('limit', opts.limit);
      if (opts.offset != null) params.set('offset', opts.offset);
      if (opts.emotion) params.set('emotion', opts.emotion);
      if (opts.q) params.set('q', opts.q);
      const qs = params.toString();
      const base = MindPalConfig.API.MEMORIES.LIST(dhId);
      const url = qs ? `${base}?${qs}` : base;
      return await MindPalAPI.request(url);
    },

    /** 统计：total + by_emotion */
    async stats(dhId) {
      return await MindPalAPI.request(MindPalConfig.API.MEMORIES.STATS(dhId));
    },

    /** 删除单条 */
    async delete(dhId, memoryId) {
      return await MindPalAPI.request(
        MindPalConfig.API.MEMORIES.DELETE(dhId, memoryId),
        { method: 'DELETE' }
      );
    },

    /** 清空全部（二次确认由前端保障，后端也要 confirm=true 兜底） */
    async clear(dhId) {
      return await MindPalAPI.request(
        MindPalConfig.API.MEMORIES.CLEAR(dhId),
        { method: 'DELETE' }
      );
    },
  },

  /**
   * 账户数据权利 API（PIPL §44/45/47）
   *
   * - dataSummary(): 查看我的数据概览（类别 + 数量）
   * - dataExport():  下载完整数据 JSON（返回 Blob 触发浏览器下载）
   * - clearMemories(): 清空长期记忆（跨所有数字人）
   * - deleteAccount(password): 注销账户（级联删除全部数据）
   */
  account: {
    async dataSummary() {
      return await MindPalAPI.request(MindPalConfig.API.ACCOUNT.DATA_SUMMARY);
    },

    /**
     * 导出数据为 JSON 文件并触发浏览器下载
     * @returns {Promise<{filename:string, sizeBytes:number}>}
     */
    async dataExport() {
      const token = MindPalAuth.getAuthToken();
      const response = await fetch(
        `${MindPalConfig.API_BASE_URL}${MindPalConfig.API.ACCOUNT.DATA_EXPORT}`,
        {
          method: 'GET',
          headers: {
            'Authorization': token && !token.startsWith('temp_') ? `Bearer ${token}` : '',
          },
        }
      );
      if (!response.ok) {
        let msg = `HTTP ${response.status}`;
        try { const j = await response.json(); msg = j.detail || j.message || msg; } catch (_) {}
        throw new Error(msg);
      }
      const blob = await response.blob();
      // 从 Content-Disposition 提取 filename
      const disposition = response.headers.get('Content-Disposition') || '';
      const match = disposition.match(/filename="?([^"]+)"?/);
      const filename = match ? match[1] : `mindpal_data_${Date.now()}.json`;

      // 触发下载
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      // 延迟 revoke 让下载启动完成
      setTimeout(() => URL.revokeObjectURL(url), 1000);

      return { filename, sizeBytes: blob.size };
    },

    async clearMemories() {
      return await MindPalAPI.request(MindPalConfig.API.ACCOUNT.CLEAR_MEMORIES, {
        method: 'DELETE',
      });
    },

    async deleteAccount(password) {
      return await MindPalAPI.request(MindPalConfig.API.ACCOUNT.DELETE, {
        method: 'DELETE',
        body: JSON.stringify({ password }),
      });
    },
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
