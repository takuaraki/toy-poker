# トイポーカー研究環境 — 技術要件定義

> 最終更新: 2026-06-11  
> 関連: [要件定義（機能）](./requirements.md)

本ドキュメントは [requirements.md](./requirements.md) の機能要件を実装可能な粒度に落とし込んだ技術仕様である。両者の対応関係は §2 に示す。

---

## 1. 技術方針

| 方針 | 内容 |
|------|------|
| 設計パラダイム | OpenSpiel 風の**明示的ゲーム木**（状態 = ノード、遷移 = 非破壊コピー） |
| 実装方針 | 完全自前。OpenSpiel / Gymnasium は**実行時依存に含めない** |
| 段階的リリース | Phase 1 = ゲームエンジン + ランダム / 人間（CLI）AI、Phase 2 = CFR + 均衡 AI |
| 型安全性 | `typing` + `@dataclass(frozen=True)` を基本。Phase 1 から型ヒント必須 |
| 不変性 | `State` は immutable。`apply_action` は新インスタンスを返す |

---

## 2. 機能要件との整合表

| 機能要件（requirements.md） | 技術要件（本書） | Phase |
|------------------------------|------------------|-------|
| §2.1 Kuhn（2 人）→ Leduc 順 | §6.1, §6.2 実装順序 | 1 |
| §2.2 Kuhn 2 人版（3 人版不要） | §6.1 OpenSpiel 互換定式化 | 1 |
| §2.3 OpenSpiel 風 API | §5 コア抽象化 | 1 |
| §2.4 ゲームエンジン | §5, §6 | 1 |
| §2.4 RandomAgent | §7.1 | 1 |
| §2.4 HumanAgent（CLI 対人対戦） | §7.2 | 1 |
| §2.4 テキスト履歴 | §8.2, §8.4 | 1 |
| §2.5 情報集合・ゲーム木 | §9.1 | 2 |
| §2.5 CFR ソルバー | §9.2 | 2 |
| §2.5 均衡 AI・exploitability | §9.3 | 2 |
| §2.7 再現性 | §11.1 RNG | 1 |
| §2.7 stdlib + numpy のみ | §3 依存関係 | 1 |
| §5 Phase 1 受け入れ基準 | §10 テスト戦略 | 1 |
| §6 Kuhn Nash 参照値 | §6.1.5, §10.3 | 2 |

---

## 3. 技術スタック

### 3.1 ランタイム

| 項目 | 仕様 |
|------|------|
| Python | **3.11+** |
| パッケージ管理 | `pyproject.toml`（PEP 621） |
| ビルド | `hatchling` または `setuptools` |
| インストール | 開発: `pip install -e ".[dev]"` |

### 3.2 依存関係

#### コア（本番 / Phase 1–2 共通）

| パッケージ | 用途 | 備考 |
|-----------|------|------|
| `numpy` | 数値計算、確率分布 | CFR の regret 更新（Phase 2） |

#### 開発のみ（`[dev]` extra）

| パッケージ | 用途 |
|-----------|------|
| `pytest` | 単体・統合テスト |
| `pytest-cov` | カバレッジ（任意） |
| `mypy` | 静的型チェック |
| `ruff` | lint / format |

**禁止**: OpenSpiel, Gymnasium, PyTorch 等をコア依存に含めない。

### 3.3 開発環境

| 項目 | 仕様 |
|------|------|
| OS | macOS / Linux（開発者環境） |
| VCS | Git |
| CI | Phase 1 完了時に GitHub Actions（`pytest` + `mypy`）を追加 |

---

## 4. アーキテクチャ

### 4.1 レイヤ構成

```
┌─────────────────────────────────────┐
│  examples/          CLI デモ        │
├─────────────────────────────────────┤
│  runner/            ハンド実行ループ │
├─────────────────────────────────────┤
│  agents/            AI 戦略          │
├─────────────────────────────────────┤
│  games/             ゲームルール     │
├─────────────────────────────────────┤
│  core/              共通抽象・型     │
└─────────────────────────────────────┘
         Phase 2 で追加:
┌─────────────────────────────────────┐
│  solvers/           CFR              │
│  trees/             ゲーム木列挙     │
└─────────────────────────────────────┘
```

### 4.2 依存方向

- `core` ← `games` ← `agents`, `runner`
- `games` 同士の相互依存なし
- Phase 2: `trees` ← `solvers` ← `agents`（CFR エージェント）
- `runner` は `games` + `agents` のみ依存（Phase 1）

### 4.3 設計原則

1. **ゲーム固有ロジックは `games/` に閉じる** — `runner` や `agents` に Kuhn 固有分岐を書かない
2. **状態遷移は純関数** — 副作用は RNG サンプリング時のみ（runner 側で実行）
3. **Phase 2 向け拡張点を Phase 1 から確保** — `State` に `information_state_string(player)` を Phase 1 から実装

---

## 5. コア抽象化

### 5.1 型・列挙

```python
# core/types.py
PlayerId = int          # 0-indexed
Payoff = float          # 各プレイヤーの utility
Action = int            # ゲームごとに Enum 化（例: KuhnAction）
ChanceOutcome = tuple[Action, float]  # (action, probability)
```

各ゲームは `Enum` で行動を定義する。

```python
# games/kuhn.py
class KuhnAction(IntEnum):
    PASS = 0
    BET = 1
```

### 5.2 Game プロトコル

```python
class Game(Protocol):
    def new_initial_state(self) -> State: ...
    def num_players(self) -> int: ...
    def max_utility(self) -> float: ...   # Phase 2 exploitability 用
```

### 5.3 State プロトコル（OpenSpiel 風 API）

Phase 1 で以下を**すべて**実装する。

| メソッド | 契約 |
|----------|------|
| `is_terminal() -> bool` | 終局なら `returns()` が有効 |
| `is_chance_node() -> bool` | True なら `current_player()` は未使用 |
| `current_player() -> PlayerId` | 非 chance・非 terminal のみ |
| `legal_actions() -> list[Action]` | 空でない（非 terminal） |
| `chance_outcomes() -> list[ChanceOutcome]` | 確率の和 ≈ 1.0 |
| `apply_action(action) -> State` | 新 State を返す。非法手は `ValueError` |
| `returns() -> list[Payoff]` | 長さ = `num_players()`。terminal のみ |
| `action_history() -> list[str]` | 人間可読な行動列 |
| `information_state_string(player) -> str` | Phase 2 用。同一観測 → 同一文字列 |

**不変性**: `@dataclass(frozen=True)` を使用。`apply_action` 内で `dataclasses.replace` する。

### 5.4 Agent プロトコル

```python
class Agent(Protocol):
    def select_action(
        self,
        state: State,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action: ...
```

Phase 1 実装: `RandomAgent(rng: np.random.Generator)`

### 5.5 基底クラス（任意）

Protocol のみでも可だが、共通バリデーション用に `core/state.py` に mixin または ABC を置く。

```python
def _check_not_terminal(state): ...
def _check_chance_node(state): ...
```

---

## 6. ゲーム実装仕様

### 6.1 Kuhn Poker（2 人版）

#### 6.1.1 OpenSpiel 互換パラメータ

| パラメータ | 値 |
|-----------|-----|
| `num_players` | 2 |
| `ante` | 1（各プレイヤー） |
| `bet_size` | 1 |
| `cards` | J=0, Q=1, K=2 |
| `first_player` | P0 |

#### 6.1.2 状態フィールド（内部表現）

```python
@dataclass(frozen=True)
class KuhnState:
    # カード: None = 未配布, 0/1/2 = J/Q/K
    cards: tuple[int | None, int | None]
    pot: int
    pending_bet: int          # 相手が BET した未コール分（0 or 1）
    current_player: int
    round_complete: bool
    terminal: bool
    folded_player: int | None
    history: tuple[str, ...]  # action_history 用
    _returns: tuple[float, float] | None
```

#### 6.1.3 ゲームフロー（状態機械）

```
[INITIAL] ante 投入, pot=2
    ↓
[CHANCE] カード配布（6 通り、各 1/6）
    ↓
[BETTING] P0 手番
    ├─ PASS → P1 手番
    │         ├─ PASS → [SHOWDOWN]
    │         └─ BET  → P0: PASS(fold) / BET(call) → [SHOWDOWN or FOLD]
    └─ BET  → P1: PASS(fold) / BET(call) → [SHOWDOWN or FOLD]
```

#### 6.1.4 合法手ルール

| 状況 | 合法手 |
|------|--------|
| `pending_bet == 0` | PASS, BET |
| `pending_bet > 0`（相手 BET 済） | PASS（= fold）, BET（= call） |

#### 6.1.5 ペイオフ計算（零和）

P0 の utility を `u` とすると、P1 の utility は `-u`。

| 終局種別 | P0 utility |
|----------|-----------|
| P1 fold | `+bet_size`（pot から相手 ante 分を獲得） |
| P0 fold | `-bet_size` |
| Showdown | カード比較に基づく pot 分配 |

**検証（Phase 2）**: P0 均衡 EV ≈ **-1/18**、P1 ≈ **+1/18**

#### 6.1.6 チャンスノード

6 通りの配布 `(c0, c1)` where `c0, c1 ∈ {J,Q,K}, c0 ≠ c1`、各確率 **1/6**。

`chance_outcomes()` は `(card_encoding, 1/6)` のリストを返す。内部では card を player に割り当てる action としてエンコードする。

#### 6.1.7 information_state_string

プレイヤー `p` の観測:

```
f"p{p}_card={card}_history={'-'.join(public_actions)}"
```

例: `p0_card=2_history=pb`（P0 が K、履歴 PASS-BET）

---

### 6.2 Leduc Hold'em

Phase 1 では Kuhn 完了後に実装。Kuhn と同一 API（§5.3）に従う。

#### 6.2.1 パラメータ

| パラメータ | 値 |
|-----------|-----|
| `num_players` | 2 |
| `ante` | 1 |
| `bet_sizes` | [2, 4]（ラウンド 1, 2） |
| `deck` | 2 スート × {J, Q, K} = 6 枚 |
| `max_raises_per_round` | 2（標準 Leduc） |

#### 6.2.2 状態機械（概要）

```
[INITIAL] ante
    ↓
[CHANCE] プライベートカード配布（6×5=30 通り）
    ↓
[BETTING ROUND 1] bet_size=2, 最大 2 レイズ
    ↓
[CHANCE] 公共カード配布（残り 5 枚から 1 枚）
    ↓
[BETTING ROUND 2] bet_size=4, 最大 2 レイズ
    ↓
[SHOWDOWN or FOLD]
```

#### 6.2.3 行動

Kuhn より多いが、OpenSpiel Leduc 互換の定式化を Phase 1 着手前に確定する。

| 行動 | 意味 |
|------|------|
| FOLD | フォールド |
| CHECK_CALL | チェックまたはコール |
| RAISE | レイズ |

---

## 7. エージェント

### 7.1 RandomAgent（Phase 1）

```python
@dataclass
class RandomAgent:
    rng: np.random.Generator

    def select_action(self, state, player, legal_actions) -> Action:
        idx = self.rng.integers(len(legal_actions))
        return legal_actions[idx]
```

- チャンスノードは **runner** が処理。Agent はプレイヤー手番のみ
- `rng` は `np.random.default_rng(seed)` で生成。seed 未指定時は非決定論的

### 7.2 HumanAgent（Phase 1）

CLI（標準入力）で人間プレイヤーが着手を選ぶエージェント。

```python
@dataclass
class HumanAgent:
  player_id: PlayerId
  input_fn: Callable[[str], str] = input   # テスト時は差し替え可能
  output_fn: Callable[[str], None] = print

  def select_action(self, state, player, legal_actions) -> Action:
      # 1. 自分の観測（カード等）を表示
      # 2. 合法手を番号付きで表示（行動名・意味付き）
      # 3. input_fn で読み取り、合法な選択になるまで再入力
      ...
```

| 項目 | 仕様 |
|------|------|
| 入力方式 | 番号選択（例: `1=PASS`, `2=BET`） |
| 不正入力 | エラーメッセージを出し、再入力を促す |
| 情報表示 | 手番プレイヤーのプライベートカード、公共情報、これまでの行動 |
| 相手のカード | 終局まで非表示（ショーダウン時に開示） |
| テスト | `input_fn` / `output_fn` をモックし、自動テスト可能にする |

対戦構成のデフォルト: **P0 = HumanAgent、P1 = RandomAgent**（CLI オプションで席を入れ替え可能）。

### 7.3 CFRAgent（Phase 2）

- `solvers/cfr.py` が出力した `dict[str, dict[Action, float]]`（infoset → 行動確率）を参照
- 推論時: 合法手に正規化した確率でサンプル、または argmax
- Phase 2 完了後、HumanAgent と組み合わせて**人間 vs 均衡 AI** も同 API で可能

---

## 8. ランナー・テキスト履歴

### 8.1 HandRunner

```python
def run_hand(
    game: Game,
    agents: list[Agent],
    rng: np.random.Generator,
) -> HandResult:
    ...
```

**アルゴリズム**:

1. `state = game.new_initial_state()`
2. terminal までループ:
   - chance node → `rng.choice` で action サンプル
   - player node → `agents[player].select_action(...)`
   - `state = state.apply_action(action)`
3. `HandResult(returns, history, state)` を返す

### 8.2 テキスト履歴フォーマット

1 行 1 イベント。例（Kuhn）:

```
=== Kuhn Poker (2p) ===
Deal: P0=K, P1=Q (hidden)
P0: BET
P1: CALL
Showdown: P0=K beats P1=Q
Pot: 4 | Returns: P0=+2.0, P1=-2.0
```

- 相手のカードは **終局まで非表示**（オプション: `--reveal` でデバッグ表示）
- `action_history()` は生ログ、`format_hand(result)` が整形出力

### 8.3 バッチ実行

```python
def run_match(
    game: Game,
    agents: list[Agent],
    num_hands: int,
    seed: int,
) -> MatchResult:
    ...
```

`MatchResult` は `mean_returns`, `std_returns`, `histories` を含む。

### 8.4 対人対戦 CLI（Phase 1）

`examples/play_kuhn.py`（Leduc も同様）に人間対戦モードを用意する。

```bash
# AI 同士（既存）
python -m examples.play_kuhn --hands 10 --seed 42

# 人間 vs ランダム AI
python -m examples.play_kuhn --human
python -m examples.play_kuhn --human --seat 1   # P1 席でプレイ
```

**対戦中の表示例（Kuhn、P0 手番）:**

```
--- Your turn (P0) ---
Your card: K
History: (none)
Legal actions:
  [1] PASS  (check)
  [2] BET   (bet 1)
> 2
```

- `run_hand` は HumanAgent を含む `agents` リストをそのまま受け取る（runner 側の変更は最小）
- バッチ実行（`run_match`）は AI 同士専用。HumanAgent を含む場合は 1 ハンドずつ CLI で実行

---

## 9. Phase 2 技術要件

### 9.1 ゲーム木・情報集合（`trees/`）

```python
def traverse_game_tree(game: Game) -> Iterator[State]: ...
def collect_infosets(game: Game) -> dict[str, list[Action]]: ...
```

- Kuhn: 全木展開 ≈ 数百ノード（即座）
- Leduc: 全木展開 ≈ 10⁶ ノード（数秒以内目標）

### 9.2 CFR ソルバー（`solvers/cfr.py`）

| 項目 | 仕様 |
|------|------|
| アルゴリズム | CFR（反復 regret matching） |
| 入力 | `Game` + 反復回数 |
| 出力 | `Strategy` = `dict[InfosetKey, dict[Action, float]]` |
| 保存形式 | JSON または pickle |
| 収束判定 | exploitability < ε または反復回数上限 |

### 9.3 Exploitability（2 人零和）

```python
def exploitability(game: Game, strategy: Strategy) -> float: ...
```

Best-response 計算により NashConv を返す。Leduc で ≈ 0 に近づくことを Phase 2 完了条件とする。

---

## 10. テスト戦略

### 10.1 Phase 1 テスト

| テスト種別 | 内容 | ファイル例 |
|-----------|------|-----------|
| 合法手 | 各局面で期待される action 集合 | `tests/games/test_kuhn_legal.py` |
| 遷移 | 特定 action 列後の state フィールド | `tests/games/test_kuhn_transitions.py` |
| ペイオフ | fold / showdown 各ケース | `tests/games/test_kuhn_payoffs.py` |
| 零和 | `returns[0] + returns[1] == 0` | 全 terminal テスト |
| 統合 | `run_hand` が例外なく完走 | `tests/test_runner.py` |
| HumanAgent | モック入出力で合法手選択・不正入力の再入力 | `tests/agents/test_human.py` |
| 再現性 | 同一 seed → 同一 returns | `tests/test_reproducibility.py` |

### 10.2 テストデータ

Kuhn の全 action 列を列挙し、既知の terminal state と照合（ゴールデンテスト）。

### 10.3 Phase 2 テスト

| テスト | 内容 |
|--------|------|
| CFR 収束 | Kuhn: P0 EV ≈ -1/18（±0.01） |
| Exploitability | 均衡戦略で ≈ 0 |
| 戦略 I/O | save → load → 同一 action 分布 |

---

## 11. プロジェクト構成

```
toy-poker/
├── docs/
│   ├── requirements.md           # 機能要件
│   └── technical-requirements.md # 本ファイル
├── src/
│   └── toy_poker/
│       ├── __init__.py
│       ├── core/
│       │   ├── types.py          # PlayerId, Action, ...
│       │   ├── protocols.py      # Game, State, Agent
│       │   └── rng.py            # make_rng(seed)
│       ├── games/
│       │   ├── kuhn.py           # KuhnGame, KuhnState, KuhnAction
│       │   └── leduc.py          # Phase 1 後半
│       ├── agents/
│       │   ├── random.py         # RandomAgent
│       │   └── human.py          # HumanAgent
│       ├── runner/
│       │   ├── hand.py           # run_hand, run_match
│       │   └── format.py         # format_hand (テキスト履歴)
│       ├── solvers/              # Phase 2
│       │   └── cfr.py
│       └── trees/                # Phase 2
│           └── traverse.py
├── tests/
│   ├── games/
│   │   └── test_kuhn.py
│   └── test_runner.py
├── examples/
│   └── play_kuhn.py              # CLI デモ
├── pyproject.toml
└── README.md
```

### 11.1 RNG ユーティリティ

```python
# core/rng.py
def make_rng(seed: int | None = None) -> np.random.Generator:
    return np.random.default_rng(seed)
```

全てのランダム処理（カード配布サンプル、RandomAgent）が同一 Generator を共有するか、seed から派生させる。

---

## 12. pyproject.toml 概要

```toml
[project]
name = "toy-poker"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["numpy>=1.26"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "mypy>=1.8", "ruff>=0.3"]

[project.scripts]
play-kuhn = "toy_poker.examples.play_kuhn:main"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["toy_poker"]
```

---

## 13. コーディング規約

| 項目 | 規約 |
|------|------|
| 命名 | snake_case（関数・変数）、PascalCase（クラス）、UPPER（定数） |
| docstring | 公開 API のみ（Google スタイル） |
| import | `from __future__ import annotations` を全ファイル先頭 |
| lint | `ruff check` + `ruff format` |
| 型チェック | `mypy src/toy_poker` |

---

## 14. 非機能要件の技術的実現

| 非機能要件 | 実現方法 |
|-----------|----------|
| 再現性 | `np.random.default_rng(seed)` を runner に渡す |
| 性能（Leduc 全展開） | `trees/traverse.py` で generator 使用、Phase 2 で計測 |
| 拡張性 | `Game` / `State` Protocol に準拠すれば `games/` 追加のみ |
| 最小依存 | コア = numpy のみ。ML 系は optional extra として将来追加 |

---

## 15. 実装マイルストーン

### Phase 1

| # | タスク | 成果物 |
|---|--------|--------|
| M1 | プロジェクト骨格 | `pyproject.toml`, 空パッケージ, CI |
| M2 | Kuhn コア | `KuhnGame`, `KuhnState`, 合法手・遷移・ペイオフ |
| M3 | Kuhn ランナー | `run_hand`, テキスト履歴, `examples/play_kuhn.py` |
| M3b | Kuhn 対人 CLI | `HumanAgent`, `play_kuhn.py --human` |
| M4 | Kuhn テスト | 合法手・ペイオフ・零和・再現性、HumanAgent（モック入出力） |
| M5 | Leduc コア | `LeducGame`, `LeducState` |
| M6 | Leduc ランナー・テスト | M3–M4 と同等 |

### Phase 2

| # | タスク | 成果物 |
|---|--------|--------|
| M7 | ゲーム木列挙 | `trees/traverse.py` |
| M8 | CFR | `solvers/cfr.py` |
| M9 | CFR エージェント | `agents/cfr_agent.py` |
| M10 | 検証 | Nash EV 一致、exploitability ≈ 0 |

---

## 16. 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-06-11 | 初版作成。requirements.md との整合表、OpenSpiel 風 API 詳細、Kuhn 2 人版仕様 |
| 2026-06-11 | Phase 1 に HumanAgent（CLI 対人対戦）を追加 |
