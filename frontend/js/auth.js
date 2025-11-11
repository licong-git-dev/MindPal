/**
 * MindPal 统一认证管理
 * 提供登录状态检查、用户信息获取、登出等功能
 */

const MindPalAuth = {
  /**
   * 检查用户是否已登录
   * @returns {boolean} 是否已登录
   */
  isLoggedIn() {
    const userData = localStorage.getItem('mindpal_user');
    if (!userData) {
      return false;
    }

    try {
      const user = JSON.parse(userData);
      return user.isLoggedIn === true;
    } catch (e) {
      console.error('解析用户数据失败:', e);
      return false;
    }
  },

  /**
   * 获取当前登录用户信息
   * @returns {Object|null} 用户信息对象或null
   */
  getCurrentUser() {
    const userData = localStorage.getItem('mindpal_user');
    if (!userData) {
      return null;
    }

    try {
      return JSON.parse(userData);
    } catch (e) {
      console.error('解析用户数据失败:', e);
      return null;
    }
  },

  /**
   * 获取认证Token (用于API调用)
   * 如果没有真实token,返回用户手机号作为临时标识
   * @returns {string|null}
   */
  getAuthToken() {
    const token = localStorage.getItem('mindpal_token');
    if (token) {
      return token;
    }

    // 如果没有token,使用用户手机号作为临时标识
    const user = this.getCurrentUser();
    if (user && user.phone) {
      return `temp_${user.phone}`;
    }

    return null;
  },

  /**
   * 保存登录信息
   * @param {Object} userData 用户数据
   * @param {string} userData.phone 手机号
   * @param {string} [token] 可选的认证token
   */
  saveLogin(userData, token) {
    const loginData = {
      ...userData,
      isLoggedIn: true,
      loginTime: new Date().toISOString()
    };

    localStorage.setItem('mindpal_user', JSON.stringify(loginData));

    if (token) {
      localStorage.setItem('mindpal_token', token);
    }
  },

  /**
   * 登出
   */
  logout() {
    localStorage.removeItem('mindpal_user');
    localStorage.removeItem('mindpal_token');
    localStorage.removeItem('mindpal_remember');

    // 跳转到登录页
    window.location.href = 'index.html';
  },

  /**
   * 要求登录 (如果未登录则跳转到登录页)
   * @param {string} [returnUrl] 登录后返回的URL
   */
  requireLogin(returnUrl) {
    if (!this.isLoggedIn()) {
      // 保存当前页面URL,登录后可返回
      if (returnUrl) {
        sessionStorage.setItem('mindpal_return_url', returnUrl);
      }

      alert('请先登录');
      window.location.href = 'index.html';
      return false;
    }
    return true;
  },

  /**
   * 获取并清除返回URL
   * @returns {string|null}
   */
  getReturnUrl() {
    const url = sessionStorage.getItem('mindpal_return_url');
    if (url) {
      sessionStorage.removeItem('mindpal_return_url');
    }
    return url;
  },

  /**
   * 检查登录状态是否过期 (可选功能)
   * @param {number} maxAgeHours 最大有效时间(小时)
   * @returns {boolean}
   */
  isLoginExpired(maxAgeHours = 24 * 7) {
    const user = this.getCurrentUser();
    if (!user || !user.loginTime) {
      return true;
    }

    const loginTime = new Date(user.loginTime);
    const now = new Date();
    const diffHours = (now - loginTime) / (1000 * 60 * 60);

    return diffHours > maxAgeHours;
  }
};

// 导出到全局作用域
window.MindPalAuth = MindPalAuth;
