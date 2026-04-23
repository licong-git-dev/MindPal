"""
MindPal Backend V2 - App Package

保持包初始化轻量，避免导入 `app` 包时触发 `app.main`
以及数据库/路由初始化副作用，便于单元测试按模块导入。
"""

__all__: list[str] = []
