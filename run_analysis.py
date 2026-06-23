#!/usr/bin/env python3
"""🔬 完整版股票五维分析 + DeepSeek · 双源实时 (eastmoney→Sina) + baostock 降级"""

import sys, json, os, time, ssl, urllib.request
import numpy as np, pandas as pd

BASE = "/Users/k/Documents/Codex/2026-06-22/an"
DS_KEY = os.path.expanduser('~/.deepseek_key')

# ─── SSL 上下文 (绕过代理证书校验) ───
_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


# ═══════════════════════════════════════════════════════════════
# 1. 实时行情 — 双源: eastmoney → Sina → baostock 日线降级
# ═══════════════════════════════════════════════════════════════

def _sina_code(c):
    """华能国际 sh600011, 京东方 sz000725"""
    return ('sh' if c.startswith('6') else 'sz') + c


def _realtime_sina(c):
    """Sina 实时数据源 — 解析 var hq_str_xxx=\"...\" 格式
    字段: 0=名称 1=今开 2=昨收 3=现价 4=最高 5=最低 6=竞买 7=竞卖
          8=成交量(手) 9=成交额(元) 30=日期 31=时间
    """
    url = f'https://hq.sinajs.cn/list={_sina_code(c)}'
    req = urllib.request.Request(
        url, headers={'Referer': 'https://finance.sina.com.cn'})
    raw = urllib.request.urlopen(req, timeout=5, context=_SSL).read().decode('gbk')
    start = raw.find('"') + 1
    flds = raw[start:raw.rfind('"')].split(',')
    if len(flds) < 10:
        return None
    pr = float(flds[3])
    pc = float(flds[2])
    return {
        'name':     flds[0],
        'price':    pr,
        'preclose': pc,
        'high':     float(flds[4]),
        'low':      float(flds[5]),
        'open':     float(flds[1]),
        'volume':   int(flds[8]),
        'amount':   float(flds[9]),
        'chg_pct':  round((pr - pc) / pc * 100, 2),
        'pe':       'N/A',
        'pb':       'N/A',
        'turn':     'N/A',
        'amplitude': round((float(flds[4]) - float(flds[5])) / pc * 100, 2) if pc > 0 else 'N/A',
        'source':   '⚡Sina实时',
    }


def get_realtime(codes):
    """双源实时行情: eastmoney (主) → Sina (备)"""
    data = {}
    for c in codes:
        c = c.strip()
        mkt = '1' if c.startswith('6') else '0'
        url = (f'https://push2.eastmoney.com/api/qt/stock/get?'
               f'secid={mkt}.{c}&fields=f43,f44,f45,f46,f57,f58,f60,f169,f170')

        # ── 先试 eastmoney ──
        got = False
        for attempt in range(2):
            try:
                req = urllib.request.Request(url)
                resp = json.loads(urllib.request.urlopen(
                    req, timeout=5, context=_SSL).read())
                x = resp.get('data')
                if x:
                    pr = float(x.get('f43', 0)) / 100 if x.get('f43') else None
                    pc = float(x.get('f60', 0)) / 100 if x.get('f60') else None
                    chg = round((pr - pc) / pc * 100, 2) if pr and pc else None
                    data[c] = {
                        'name':      x.get('f58', ''),
                        'price':     pr,
                        'preclose':  pc,
                        'high':      float(x.get('f44', 0)) / 100 if x.get('f44') else None,
                        'low':       float(x.get('f45', 0)) / 100 if x.get('f45') else None,
                        'open':      float(x.get('f46', 0)) / 100 if x.get('f46') else None,
                        'chg_pct':   chg,
                        'pe':        'N/A',
                        'pb':        'N/A',
                        'turn':      'N/A',
                        'amplitude': x.get('f170', 'N/A'),
                        'source':    '⚡实时',
                    }
                    got = True
                break
            except Exception:
                if attempt == 0:
                    time.sleep(0.3)

        if got:
            continue

        # ── 再用 Sina ──
        try:
            data[c] = _realtime_sina(c)
        except Exception as e:
            data[c] = {'error': str(e)[:80], 'source': '❌无实时'}

    return data


# ═══════════════════════════════════════════════════════════════
# 2. 历史K线 (baostock, 稳定)
# ═══════════════════════════════════════════════════════════════

def get_history(codes):
    import baostock as bs
    bs.login()
    result = {}
    for c in codes:
        c = c.strip()
        mkt = "sh" if c.startswith('6') else "sz"
        rs = bs.query_history_k_data_plus(
            f"{mkt}.{c}",
            "date,open,high,low,close,preclose,volume,amount,turn,peTTM,pbMRQ",
            start_date='2026-01-01', frequency='d')
        df = rs.get_data()
        if not df.empty:
            for col in ['open', 'high', 'low', 'close', 'preclose',
                         'volume', 'amount', 'turn', 'peTTM', 'pbMRQ']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            df['chg_pct'] = df['close'].pct_change() * 100
            last = df.iloc[-1]
            prev20 = df.tail(20)
            result[c] = {
                'df':       df,
                'last':     last,
                'close':    float(last['close']),
                'preclose': float(last['preclose']),
                'chg_pct':  float(last['chg_pct']),
                'volume':   int(last['volume']),
                'amount':   float(last['amount']),
                'turn':     float(last['turn']),
                'ma5':      float(last['ma5']),
                'ma20':     float(last['ma20']),
                'peTTM':    float(last['peTTM']) if not np.isnan(last['peTTM']) else None,
                'pbMRQ':    float(last['pbMRQ']) if not np.isnan(last['pbMRQ']) else None,
                '20d_high': float(prev20['high'].max()),
                '20d_low':  float(prev20['low'].min()),
                '20d_chg':  float((df.iloc[-1]['close'] - df.iloc[-21]['close'])
                                  / df.iloc[-21]['close'] * 100) if len(df) > 20 else None,
                '20d_vol':  float(prev20['chg_pct'].std()),
            }
        else:
            result[c] = None
    bs.logout()
    return result


# ═══════════════════════════════════════════════════════════════
# 3. 五维分析引擎
# ═══════════════════════════════════════════════════════════════

def analyze(rt_row, hist, source):
    c = rt_row.get('price', hist['close']) if rt_row else hist['close']
    chg = rt_row.get('chg_pct', hist['chg_pct']) if rt_row and rt_row.get('chg_pct') else hist['chg_pct']
    pe = rt_row.get('pe') if rt_row and rt_row.get('pe') not in ('N/A', None) else hist.get('peTTM')
    pb = rt_row.get('pb') if rt_row and rt_row.get('pb') not in ('N/A', None) else hist.get('pbMRQ')

    above_ma5 = c > hist['ma5']
    above_ma20 = c > hist['ma20']

    # UZI · 趋势评分
    ts = 0
    if above_ma5: ts += 2
    if above_ma20: ts += 2
    if hist.get('20d_chg') and hist['20d_chg'] > 5: ts += 1
    if chg and chg > 1: ts += 1
    uzi = (f"UZI·趋势{ts}/7 | "
           f"MA5:{'✅上' if above_ma5 else '❌下'} "
           f"MA20:{'✅上' if above_ma20 else '❌下'} | "
           f"20日:{hist.get('20d_chg', 0):+.1f}%")

    # TradingAgents · 信号
    sig = []
    if chg and chg > 1:   sig.append("趋势✅")
    elif chg and chg < -1: sig.append("趋势⚠️")
    if pe and pe < 15:     sig.append("低估⭐")
    if above_ma20:         sig.append("动量✅")
    ta = f"TradingAgents: {' | '.join(sig) if sig else '信号中性'}"

    # Serenity · 供应链
    serenity = "Serenity·供应链卡点→需结合行业链映射"

    # Buffett · 护城河
    bf = []
    bs = 0
    if pe and pe < 15:
        bf.append(f"PE{pe:.1f}✅"); bs += 3
    elif pe and pe < 25:
        bf.append(f"PE{pe:.1f}🟡")
    if pb and pb < 2:
        bf.append(f"PB{pb:.2f}✅"); bs += 3
    elif pb and pb < 5:
        bf.append(f"PB{pb:.2f}🟡")
    if hist.get('20d_chg') and hist['20d_chg'] < 30:
        bf.append("未追高✅"); bs += 2
    buffett = (f"Buffett·{bs}/8 | "
               f"{' | '.join(bf) if bf else '数据不足'}")

    # QuantDinger · 量化
    qs = 50
    if above_ma5:      qs += 10
    if pe and pe < 15:  qs += 10
    if chg and chg > 0:  qs += 5
    qd = (f"QuantDinger·{min(qs, 95)}/100 | "
          f"{'金叉✅' if above_ma5 else '死叉⚠️'} | "
          f"波{hist.get('20d_vol', 0):.1f}%")

    return uzi, ta, serenity, buffett, qd

# ═══════════════════════════════════════════════════════════════
# 3.5 Serenity · 供应链卡点分析 (DeepSeek)
# ═══════════════════════════════════════════════════════════════

def serenity_chain(stock_info_list):
    """用 DeepSeek API 做产业链/供应链卡点分析"""
    api_key = open(DS_KEY).read().strip() if os.path.exists(DS_KEY) else ''
    if not api_key:
        return {s['code']: '⚠️ Key未设置' for s in stock_info_list}

    stocks_desc = []
    for s in stock_info_list:
        desc = (f"- {s['code']} {s.get('name','')} "
                f"(现价{s['price']}, PE{s.get('pe','?')}, PB{s.get('pb','?')})")
        stocks_desc.append(desc)

    NL = "\n"
    prompt = f"""你是A股产业链分析专家。按Serenity供应链卡点方法论分析以下股票，每条80字以内。

{NL.join(stocks_desc)}

对每只股票分析：1)产业链位置(上游/中游/下游/平台) 2)关键上游依赖 3)下游集中度风险 4)卡点环节(技术壁垒/政策门槛/产能瓶颈) 5)一句话总结是否为强卡点。

输出格式(每只一行):
[代码] 位置:xxx | 上游:xxx | 下游:xxx | 卡点:xxx | 总结:xxx"""

    try:
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
        resp = json.loads(urllib.request.urlopen(req, timeout=20, context=_SSL).read())
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




# ═══════════════════════════════════════════════════════════════
# 4. DeepSeek 总结 + 建议买入价
# ═══════════════════════════════════════════════════════════════

def deepseek(report):
    api_key = open(DS_KEY).read().strip() if os.path.exists(DS_KEY) else ''
    if not api_key:
        return "\n⚠️ DeepSeek API Key 未设置\n"

    prompt = f"""你是A股分析专家。基于以下五维分析数据，给出简洁总结和具体建议买入价格：

{json.dumps(report, ensure_ascii=False, indent=2)}

输出格式（200字内）：
【总结】【建议买入价】【止损价】【仓位】"""

    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
                "temperature": 0.6,
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            })
        resp = json.loads(urllib.request.urlopen(
            req, timeout=15, context=_SSL).read())
        return "\n" + resp['choices'][0]['message']['content'] + "\n"
    except Exception as e:
        return f"\n⚠️ DeepSeek 调用失败: {e}\n"


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    codes = [c.strip() for c in (
        sys.argv[1:] if len(sys.argv) > 1
        else input("股票代码: ").split())]

    print(f"\n{'='*70}")
    print(f"🔬 双源实时 + 五维分析 + DeepSeek | {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")

    # [1/4] 实时行情
    print("\n📡 [1/4] 拉取实时行情 (eastmoney → Sina)...")
    rt = get_realtime(codes)

    # [2/4] 历史K线
    print("📊 [2/4] 拉取历史K线 (baostock)...")
    hist = get_history(codes)

    # [3/4] 五维分析 (Serenity 将在 3.5 步由 DeepSeek 补齐)
    print("🧠 [3/4] 五维引擎分析中...\n")
    full_report = {}
    stock_list = []

    for code in codes:
        r = rt.get(code, {})
        h = hist.get(code)
        if not h:
            print(f"❌ {code}: 无历史数据\n")
            continue

        use_rt = r and 'error' not in r and r.get('price')
        src = r.get('source', '⚡实时') if use_rt else '📊日线(延迟)'

        c = r['price'] if use_rt else h['close']
        chg = r['chg_pct'] if use_rt and r.get('chg_pct') else h['chg_pct']
        pe = h.get('peTTM')
        pb = h.get('pbMRQ')
        name = r.get('name', '') if use_rt else ''

        stock_list.append(
            {'code': code, 'name': name, 'price': c, 'pe': pe, 'pb': pb})

        print(f"{'─'*70}")
        print(f"📊 {code} {name} | {src} {c:.2f} | {chg:+.2f}% | "
              f"PE:{pe or '-'} | PB:{pb or '-'}")
        if use_rt:
            print(f"   今开:{r['open']:.2f} 高:{r['high']:.2f} 低:{r['low']:.2f} "
                  f"昨收:{r['preclose']:.2f}")
        print(f"   成交:{h['volume']}手 换手:{h['turn']:.1f}% "
              f"振幅:{r.get('amplitude', 'N/A') if use_rt else 'N/A'}")
        print(f"{'─'*70}")

        uzi, ta, serenity, buffett, qd = analyze(r if use_rt else None, h, src)
        print(f"🧬 {uzi}")
        print(f"🤖 {ta}")
        print(f"🔗 {serenity}")
        print(f"🏰 {buffett}")
        print(f"📐 {qd}")

        full_report[code] = {
            'name': name, 'price': c, 'chg_pct': chg,
            'pe': pe, 'pb': pb, 'source': src,
        }
        print()

    # [3.5/4] Serenity 供应链分析
    print("🔗 [3.5/4] Serenity 供应链卡点分析 (DeepSeek)...\n")
    chain_data = serenity_chain(stock_list)
    for code in codes:
        chain_text = chain_data.get(code, '⚠️ 无供应链数据')
        print(f"🔗 {code}: {chain_text}")
        print()

    # [4/4] DeepSeek
    print(f"{'='*70}")
    print("🦾 [4/4] DeepSeek 总结建议")
    print(f"{'='*70}")
    print(deepseek(full_report))
