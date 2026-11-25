# toy-poker

Kuhn Poker（2 人）と Leduc Hold'em 向けの研究用トイポーカー環境。

## 要件

- Python 3.11+

## インストール

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## クイックスタート

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Kuhn: ランダム AI 同士で 1 ハンド
play-kuhn

# Kuhn: 10 ハンド + シード固定
play-kuhn --hands 10 --seed 42

# Kuhn: 人間 vs ランダム AI
play-kuhn --human
play-kuhn --human --seat 1

# Kuhn: 人間 vs 学習済み戦略
play-kuhn --human --strategy strategies/kuhn.json
play-kuhn --human --strategy strategies/kuhn.json --mode argmax --seat 1

# Leduc も同様
play-leduc
play-leduc --hands 10 --seed 42
play-leduc --human
play-leduc --human --strategy strategies/leduc.json
```

### 戦略 JSON の生成

```bash
# Kuhn + Leduc（Leduc は数分かかる）
train-strategies

# 片方だけ / 反復回数指定
train-strategies --game kuhn
train-strategies --game leduc --iterations 1000
```

出力は `strategies/*.json`。現状の Kuhn / Leduc は数十 KiB 以下なので通常の Git で管理する。将来 1 MiB を超える場合は Git LFS（例: `git lfs track 'strategies/*.json'`）へ切り替える。

## 開発

```bash
# 通常のテスト（CI と同じ。slow を除外）
pytest -m "not slow"

# 時間のかかるテストのみ（例: Leduc exploitability の厳密チェック）
pytest -m slow

# すべて実行
pytest

mypy src/toy_poker
ruff check src tests
ruff format src tests
```

## ドキュメント

- [機能要件](docs/requirements.md)
- [技術要件](docs/technical-requirements.md)

## ライセンス

MIT
