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

# ランダム AI 同士で 1 ハンド
play-kuhn

# 10 ハンド + シード固定
play-kuhn --hands 10 --seed 42

# 人間 vs ランダム AI
play-kuhn --human
play-kuhn --human --seat 1
```

## 開発

```bash
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
