#!/usr/bin/env python3
"""🔬 一键股票五维分析 + DeepSeek 总结"""

import sys, json, os, urllib.request, ssl
import numpy as np, pandas as pd

DS_KEY = os.path.expanduser('~/.deepseek_key')

# ─── 1. 数据获取 ───
def fetch_data(codes):
    import baostock as bs
    bs.login()
    all_data = {}
    code_map = {}
    for c in codes:
        c = c.strip()
        if c.startswith(('0','3')) and len(c)==6:
            code_map[c] = f"sz.{c}"
        elif c.startswith('6') and len(c)==6:
            code_map[c] = f"sh.{c}"
        else:
            code_map[c] = f"sz.{c}" if c[0] in '0123' else f"sh.{c}"
    for raw_code, bs_code in code_map.items():
        rs = bs.query_history_k_data_plus(bs_code,
            "date,open,high,low,close,preclose,volume,amount,turn,peTTM,pbMRQ",
            start_date='2026-01-01', frequency='d')
        df = rs.get_data()
        if df.empty: all_data[raw_code] = None; continue
        for col in ['open','high','low','close','preclose','volume','amount','turn','peTTM','pbMRQ']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['chg_pct'] = (df['close'] - df['preclose']) / df['preclose'] * 100
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        last = df.iloc[-1]; prev20 = df.tail(20)
        all_data[raw_code] = {
            'code': raw_code, 'date': str(last['date']),
            'close': float(last['close']), 'preclose': float(last['preclose']),
            'chg_pct': float(last['chg_pct']), 'open': float(last['open']),
            'high': float(last['high']), 'low': float(last['low']),
            'volume': int(last['volume']), 'amount': float(last['amount']),
            'turn': float(last['turn']) if not np.isnan(last['turn']) else None,
            'peTTM': float(last['peTTM']) if not np.isnan(last['peTTM']) else None,
            'pbMRQ': float(last['pbMRQ']) if not np.isnan(last['pbMRQ']) else None,
            'ma5': float(last['ma5']) if not np.isnan(last['ma5']) else None,
            'ma20': float(last['ma20']) if not np.isnan(last['ma20']) else None,
            'above_ma5': bool(float(last['close']) > float(last['ma5'])) if not np.isnan(last['ma5']) else None,
            'above_ma20': bool(float(last['close']) > float(last['ma20'])) if not np.isnan(last['ma20']) else None,
            'vol_ratio': float(last['volume'] / prev20['volume'].mean()) if len(prev20)>0 else None,
            '20d_high': float(prev20['high'].max()), '20d_low': float(prev20['low'].min()),
            '20d_chg': float((last['close'] - df.iloc[-21]['close']) / df.iloc[-21]['close'] * 100) if len(df)>20 else None,
            '20d_vol': float(prev20['chg_pct'].std()),
            'amplitude': float((last['high']-last['low'])/last['preclose']*100),
        }
    bs.logout()
    return all_data

# ─── 2. 五维分析引擎 ───
def analyze(d):
    lines = []
    c = d['close']; chg = d['chg_pct']; pe = d.get('peTTM'); pb = d.get('pbMRQ')
    
    # UZI-Skill
    ts = 0
    if d.get('above_ma5'): ts += 2
    if d.get('above_ma20'): ts += 2
    if d.get('20d_chg') and d['20d_chg'] > 5: ts += 1
    if chg > 1: ts += 1
    if d.get('vol_ratio') and d['vol_ratio'] > 1.2: ts += 1
    lines.append(f"🧬 UZI-Skill: 趋势评分 {ts}/7 | "
                f"MA5:{'✅上' if d.get('above_ma5') else '❌下'} MA20:{'✅上' if d.get('above_ma20') else '❌下'} | "
                f"振幅:{d['amplitude']:.1f}% | 20日:{d.get('20d_chg','?'):+.1f}%")
    
    # TradingAgents
    sig = []
    if chg > 1: sig.append("趋势✅")
    elif chg < -1: sig.append("趋势⚠️")
    if d.get('vol_ratio',1) > 1.2 and chg > 0: sig.append("量能✅")
    elif d.get('vol_ratio',1) > 1.2: sig.append("量能⚠️")
    if pe and pe < 15: sig.append("低估⭐")
    if d.get('above_ma20'): sig.append("动量✅")
    lines.append(f"🤖 TradingAgents: {' | '.join(sig) if sig else '信号中性'}")
    
    # Serenity
    lines.append(f"🔗 Serenity: 行业卡点分析→将由 DeepSeek 供应链引擎补齐")
    
    # Buffett
    bf = []
    if pe and pe < 15: bf.append(f"PE{pe:.1f} ✅")
    if pb and pb < 2: bf.append(f"PB{pb:.2f} ✅")
    if d.get('20d_chg') and d['20d_chg'] < 30: bf.append("未追高 ✅")
    lines.append(f"🏰 Buffett: {' | '.join(bf) if bf else '数据不足'}")
    
    # QuantDinger
    qd = []
    if d.get('above_ma5'): qd.append("MA金叉✅")
    else: qd.append("MA死叉⚠️")
    qd.append(f"波动率:{d.get('20d_vol','?'):.1f}%")
    if pe and pe < 15: qd.append(f"PE分位:低位⭐")
    score = 50 + (ts*3) + (10 if pe and pe<15 else 0) + (5 if chg>0 else -5)
    lines.append(f"📐 QuantDinger: {' | '.join(qd)} | 综合评分:{min(score,95)}/100")
    
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════
# 2.5 Serenity · 供应链卡点分析 (DeepSeek)
# ═══════════════════════════════════════════════════════════════

def serenity_chain(stock_info_list):
    """用 DeepSeek API 做产业链/供应链卡点分析"""
    api_key = open(DS_KEY).read().strip() if os.path.exists(DS_KEY) else ''
    if not api_key:
        return {s['code']: '⚠️ Key未设置' for s in stock_info_list}

    stocks_desc = []
    for s in stock_info_list:
        desc = (f"- {s['code']} {s.get('name','')} "
                f"(收盘{s['close']}, PE{s.get('peTTM','?')}, PB{s.get('pbMRQ','?')})")
        stocks_desc.append(desc)

    NL = "\n"
    prompt = f"""你是A股产业链分析专家。按Serenity供应链卡点方法论分析以下股票，每条80字以内。

{NL.join(stocks_desc)}

对每只股票分析：1)产业链位置(上游/中游/下游/平台) 2)关键上游依赖 3)下游集中度风险 4)卡点环节(技术壁垒/政策门槛/产能瓶颈) 5)一句话总结是否为强卡点。

输出格式(每只一行):
[代码] 位置:xxx | 上游:xxx | 下游:xxx | 卡点:xxx | 总结:xxx"""

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600, "temperature": 0.4,
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            })
        resp = json.loads(urllib.request.urlopen(req, timeout=20, context=ctx).read())
        text = resp['choices'][0]['message']['content']
        result = {}
        for line in text.strip().split("\n"):
            for s in stock_info_list:
                if line.strip().startswith(f"[{s['code']}]"):
                    result[s['code']] = line.strip()
                    break
        for s in stock_info_list:
            if s['code'] not in result:
                result[s['code']] = '⚠️ 未匹配'
        return result
    except Exception as e:
        return {s['code']: f'⚠️ 失败: {e}' for s in stock_info_list}


# ─── 3. DeepSeek 总结 ───
def deepseek_summary(analyses):
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        cfg = os.path.expanduser('~/.deepseek_key')
        if os.path.exists(cfg): api_key = open(cfg).read().strip()
    if not api_key:
        return "\n⚠️ DeepSeek API Key 未设置。echo 'sk-xxx' > ~/.deepseek_key\n"
    
    summary_text = json.dumps(analyses, ensure_ascii=False)
    prompt = f"""你是A股分析专家。基于以下五维分析数据，给出简洁总结和具体建议买入价：

{summary_text}

格式（不超过200字）：
【总结】一句话
【建议买入价】具体价格区间
【止损价】具体价格
【仓位】轻/中/重"""
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role":"user","content":prompt}],
                "max_tokens": 400, "temperature": 0.6
            }).encode(),
            headers={"Content-Type":"application/json", "Authorization": f"Bearer {api_key}"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=15, context=ctx).read())
        return "\n" + resp['choices'][0]['message']['content'] + "\n"
    except Exception as e:
        return f"\n⚠️ DeepSeek 调用失败: {e}\n"

# ─── Main ───
if __name__ == '__main__':
    codes = sys.argv[1:] if len(sys.argv)>1 else input("输入股票代码（空格分隔）: ").split()
    print(f"\n{'='*60}\n🔬 股票五维分析流水线\n{'='*60}")
    data = fetch_data(codes)
    
    stock_list = []
    all_analysis = {}
    for code, d in data.items():
        if not d:
            print(f"\n❌ {code}: 无数据")
            continue
        print(f"\n{'─'*60}")
        print(f"📊 {code} | 收盘:{d['close']} | 涨跌:{d['chg_pct']:+.2f}% | PE:{d.get('peTTM','-')} | PB:{d.get('pbMRQ','-')}")
        print(f"{'─'*60}")
        analysis = analyze(d)
        print(analysis)
        all_analysis[code] = {
            'name': d.get('name', code), 'close': d['close'], 'chg_pct': d['chg_pct'],
            'peTTM': d.get('peTTM'), 'pbMRQ': d.get('pbMRQ'),
            'analysis': analysis
        }
        stock_list.append({
            'code': code, 'name': d.get('name', code),
            'close': d['close'], 'peTTM': d.get('peTTM'), 'pbMRQ': d.get('pbMRQ')
        })
    
    # Serenity 供应链分析
    print(f"\n{'─'*60}")
    print("🔗 Serenity 供应链卡点分析 (DeepSeek)...")
    chain_data = serenity_chain(stock_list)
    for code in codes:
        if code in chain_data:
            print(f"\n🔗 {code}: {chain_data[code]}")

    print(f"\n{'='*60}\n🦾 DeepSeek 总结建议\n{'='*60}")
    print(deepseek_summary(all_analysis))
