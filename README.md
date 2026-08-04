# 可转债数据库 · Streamlit

## 本地启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署

可将本目录推送至 GitHub，并在 Streamlit Community Cloud 中选择 `app.py` 作为入口文件。

本项目为 Python Streamlit 应用，不能直接部署到仅托管静态文件的 Cloudflare Pages。

## 个人研究工作台

网站支持账户注册登录、保存/载入筛选方案和个券自选。密码使用 PBKDF2 加盐哈希保存，账户记录写入本地 `SQLite` 数据库；数据库文件不会提交到 GitHub。

Streamlit Community Cloud 的本地磁盘不保证跨服务重建永久保留。正式对外运营时，建议把 `users`、`saved_screens` 和 `watchlist` 三张表迁移到 Supabase/PostgreSQL 等持久化数据库。
