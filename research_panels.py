"""Source-backed dashboard panels. All changes refer to the workbook observation date."""
import html
import pandas as pd
import altair as alt
import streamlit as st

BLUE='#245e99'
ORANGE='#e99a2f'

def research_snapshot(bonds, market, supply):
    ordered=market.sort_values('date').dropna(subset=['price_median','premium_median'])
    last=ordered.iloc[-1]
    previous=ordered.iloc[max(0,len(ordered)-6)]
    price_change=(last.price_median/previous.price_median-1)*100
    premium_change=last.premium_median-previous.premium_median
    active=bonds[(bonds.price>0)&(bonds.turnover>0)]
    positive=int((active.change_5d>0).sum())
    valid=int(active.change_5d.notna().sum())
    low=int((active.price<115).sum())
    stock_valid=int(active.stock_price.notna().sum())
    cards=[('价格与估值',f'{price_change:+.2f}%',f'价格中位数相对 {previous.date:%m/%d} 的变化；溢价率中位数变化 {premium_change:+.2f} 个百分点。'),
           ('个券涨跌结构',f'{positive} / {valid}',f'有成交且近5日涨跌有效的个券中，{positive}只上涨；低于115元的个券共{low}只。'),
           ('正股联动',f'{stock_valid}只',f'有正股价格的交易个券。正股与转债价格、单日和5日涨跌可在个券机会池中筛选、下载。')]
    st.markdown('<div class="snapshot-grid">'+''.join(f'<div class="snapshot-tile"><small>{a}</small><strong>{b}</strong><p>{c}</p></div>' for a,b,c in cards)+'</div>',unsafe_allow_html=True)
    st.caption(f'数据观察：{previous.date:%Y-%m-%d} 至 {last.date:%Y-%m-%d}。由所提供数据库计算；市场中位数变化不等同转债指数收益。')

def valuation_dashboard(market, metadata, mobile):
    st.subheader('估值与交易跟踪')
    left,right=st.columns(2)
    points=market.sort_values('date').tail(130)
    for container, label, field, unit, color in [(left,'隐含波动率','implied_vol','%',BLUE),(right,'全市场成交额','turnover_total','亿元',ORANGE)]:
        with container:
            st.markdown(f'**{label}**')
            chart=alt.Chart(points).mark_line(color=color,strokeWidth=2).encode(
                x=alt.X('date:T',title=None,axis=alt.Axis(format='%m/%d',tickCount=4)),
                y=alt.Y(f'{field}:Q',title=unit,scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip('date:T',title='日期',format='%Y-%m-%d'),alt.Tooltip(f'{field}:Q',title=label,format='.2f')]).properties(height=185 if mobile else 210)
            st.altair_chart(chart,width='stretch')
    with st.expander('查看历史估值分位数',expanded=False):
        q=pd.DataFrame(metadata['quantiles']).rename(columns={'window':'历史窗口','implied_vol':'隐含波动率','parity':'平价','price':'价格','ytm':'YTM','premium':'转股溢价率'})
        st.dataframe(q,hide_index=True,width='stretch',column_config={c:st.column_config.NumberColumn(format='percent') for c in q.columns if c!='历史窗口'})
        st.caption('分位数直接读取数据库「转债估值」表；不同历史窗口分别计算。')

def issuance_dashboard(metadata, date):
    listings=pd.DataFrame(metadata['listings'])
    listings['date']=pd.to_datetime(listings['date'],errors='coerce')
    ytd=listings[(listings.date.dt.year==date.year)&(listings.date<=date)].copy()
    if len(ytd):
        left,right=st.columns([1,1.2])
        with left:
            st.markdown('**年内每月上市规模**')
            ytd['month']=ytd.date.dt.to_period('M').astype(str)
            months=pd.period_range(f'{date.year}-01',date.to_period('M'),freq='M').astype(str)
            monthly=ytd.groupby('month').agg(size=('size','sum'),count=('code','size')).reindex(months,fill_value=0).rename_axis('month').reset_index()
            chart=alt.Chart(monthly).mark_bar(color=BLUE,cornerRadiusTopLeft=3,cornerRadiusTopRight=3).encode(x=alt.X('month:N',title=None,axis=alt.Axis(labelAngle=-35)),y=alt.Y('size:Q',title='亿元'),tooltip=[alt.Tooltip('month:N',title='月份'),alt.Tooltip('size:Q',title='上市规模（亿元）',format='.2f'),alt.Tooltip('count:Q',title='只数')]).properties(height=245)
            st.altair_chart(chart,width='stretch')
        with right:
            options=['全部月份']+sorted(ytd.month.unique(),reverse=True)
            selected=st.selectbox('按月查看新券',options)
            detail=ytd if selected=='全部月份' else ytd[ytd.month==selected]
            show=detail[['date','name','code','size','first_price','first_premium','rating']].copy()
            show['date']=show.date.dt.strftime('%Y-%m-%d')
            show.columns=['上市日期','名称','代码','规模（亿元）','首日价格','首日溢价率（%）','评级']
            st.dataframe(show,hide_index=True,width='stretch',height=245)
        st.caption('上市规模按原表「发行规模」在上市月归集，区别于发行月融资额；尚未结束的月份仅截至数据日。')
    pending=pd.DataFrame(metadata['pending'])
    with st.expander(f'已发行待上市 · {len(pending)}只',expanded=False):
        st.dataframe(pending.rename(columns={'date':'发行日期','code':'代码','name':'名称','size':'规模（亿元）','industry':'行业','rating':'评级'}),hide_index=True,width='stretch')
