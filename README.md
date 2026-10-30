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

网站支持账户注册登录、保存/载入筛选方案和个券自选。设置 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY` 后使用原有 Supabase 账户及 RLS 隔离数据；未设置时使用本机 SQLite。密码使用 PBKDF2 加盐哈希保存，数据库文件不会提交到 GitHub。

Streamlit Community Cloud 的本地磁盘不保证跨服务重建永久保留。线上继续使用已配置的 Supabase，勿移除 Secrets。此更新不修改云端账户、策略和自选表。

## 周度数据更新

运行 `python update_data.py "新数据库.xlsx"`，从源文件缓存值提取个券、历史行情、供给、估值分位数和新券上市清单，不修改 Excel。页面日期来自行情表最新日期，不使用当天日期冒充数据日。正股名称按已有代码匹配，未匹配时留空，价格和涨跌取本期数据。运行后检查 `data/metadata.json`。

本版借鉴所提供 htscficc-analysis 的蓝橙配色、紧凑导航和图表分栏，仅使用转债 Excel 数据。手机支持紧凑表格、双列卡片、登录、筛选和下载。市场存量与个券余额分别保留两张源表口径。
