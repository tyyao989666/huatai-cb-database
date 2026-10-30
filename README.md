# 可转债数据库 · Streamlit

## 本地启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署

可将本目录推送至 GitHub，并在 Streamlit Community Cloud 中选择 `app.py` 作为入口文件。

本项目为 Python Streamlit 应用，不能直接部署到仅托管静态文件的 Cloudflare Pages。

## 公开访问

网站无需注册或登录，电脑和手机均可直接查看市场数据、筛选个券并下载筛选结果。登录、注册、保存方案及账户自选入口已移除，页面运行不再导入或调用 Supabase，也不再初始化本地用户数据库。

原有 Supabase 适配器和建表脚本仅作为历史文件保留，不参与页面运行。本次更新不删除已有云端账户、筛选方案、自选记录或本地数据库。

## 周度数据更新

运行 `python update_data.py "新数据库.xlsx"`，从源文件缓存值提取个券、历史行情、供给、估值分位数和新券上市清单，不修改 Excel。页面日期来自行情表最新日期，不使用当天日期冒充数据日。正股价格和涨跌仍取本期 Excel 数据。

正股名称按完整证券代码匹配已有数据及 `data/stock_names.json`。新增代码缺少名称时，更新程序自动查询巨潮资讯证券列表，仅补充缺失名称并缓存来源、查询时间和代码，不按转债简称推测正股。网页本身不调用外部名称接口。网络失败或未匹配时保留缺失状态，在终端和 `data/metadata.json` 的 `stock_name_missing_codes` 中列出，页面及下载显示“待补充”。离线更新可添加 `--offline-stock-names`。名称查询时间不代表价格行情时间。

更新后检查 `data/metadata.json`，确认 `stock_names_missing` 为 0；若大于 0，核实并补齐对应证券名称后再发布。

本版借鉴所提供 htscficc-analysis 的蓝橙配色、紧凑导航和图表分栏，仅使用转债 Excel 数据。手机支持紧凑表格、双列卡片、筛选和下载。市场存量与个券余额分别保留两张源表口径。
