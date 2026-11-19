# -*- coding: utf-8 -*-
"""批次（batch）为一等公民：清单、幂等、增量、diff。

一个批次 = 一次导入。manifest 记录来源、输入 sha256、参数、版本、窗口与统计，
使运行可复现、可审计、可增量、可对比。
"""
import hashlib, json, os
from datetime import datetime, timezone

SCHEMA = 'billkit.batch/1'


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def datetime_window(rows):
    ds = [(r.get('datetime') or '')[:19] for r in rows if (r.get('datetime') or '')]
    if not ds:
        return {'min': None, 'max': None}
    return {'min': min(ds), 'max': max(ds)}


def make_manifest(input_path, source, rows, params, stats, outputs, version):
    return {
        'schema': SCHEMA,
        'billkit_version': version,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'input': {
            'path': os.path.basename(input_path) if input_path else None,
            'sha256': file_sha256(input_path) if input_path and os.path.exists(input_path) else None,
            'rows': len(rows),
            'source': source,
        },
        'params': params,
        'window': datetime_window(rows),
        'stats': stats,
        'outputs': outputs,
    }


def write_manifest(outdir, manifest):
    path = os.path.join(outdir, 'batch.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
    return path


def read_manifest(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def filter_incremental(rows, prior_manifest):
    """增量：只保留 datetime 严格晚于上一批 window.max 的行。"""
    wmax = ((prior_manifest or {}).get('window') or {}).get('max')
    if not wmax:
        return list(rows), {'since': None, 'kept': len(rows), 'dropped': 0}
    kept = []
    for r in rows:
        dt = (r.get('datetime') or '')[:19]
        if dt and dt > wmax:
            kept.append(r)
    return kept, {'since': wmax, 'kept': len(kept), 'dropped': len(rows) - len(kept)}


def diff_manifests(a, b):
    """对比两个 manifest 的统计与窗口，返回可读差异。"""
    sa = a.get('stats') or {}; sb = b.get('stats') or {}
    keys = sorted(set(sa) | set(sb))
    changes = {}
    for k in keys:
        if k in ('by_method', 'by_purpose'):
            continue
        va, vb = sa.get(k), sb.get(k)
        if va != vb:
            changes[k] = {'a': va, 'b': vb, 'delta': (vb - va) if isinstance(va, (int, float)) and isinstance(vb, (int, float)) else None}
    return {
        'a': {'generated_at': a.get('generated_at'), 'input': a.get('input'), 'window': a.get('window')},
        'b': {'generated_at': b.get('generated_at'), 'input': b.get('input'), 'window': b.get('window')},
        'changed_stats': changes,
        'rows_delta': (sb.get('total', 0) or 0) - (sa.get('total', 0) or 0),
    }
