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
# （先に CFR で JSON を保存しておく）
play-kuhn --human --strategy path/to/kuhn.json
play-kuhn --human --strategy path/to/kuhn.json --mode argmax --seat 1

# Leduc も同様
play-leduc
play-leduc --hands 10 --seed 42
play-leduc --human
play-leduc --human --strategy path/to/leduc.json
```

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
