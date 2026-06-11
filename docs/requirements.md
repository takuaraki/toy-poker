# トイポーカー研究環境 — 要件定義

> 最終更新: 2026-06-11  
> ステータス: Phase 1 要件確定 / Phase 2 概要確定  
> 関連: [技術要件定義](./technical-requirements.md)

---

## 1. プロジェクト概要

不完全情報ゲーム（imperfect-information game）の研究・実験のため、**Kuhn Poker** や **Leduc Hold'em** などの小規模ポーカーバリアントを扱う Python ベースの研究環境を構築する。

### 開発方針

**段階的実装**とする。まずゲームを遊べる状態にし、その後 CFR を自前実装して均衡戦略 AI を作る。

| Phase | 目標 | AI |
| ------- | ------ | ----- |
| **Phase 1** | ゲームが遊べる状態にする（対人 CLI 含む） | ランダム / **人間（CLI 入力）** |
| **Phase 2** | CFR 自前実装 → 均衡戦略 AI | CFR で学習した Nash 近似 |

外部 solver（OpenSpiel 等）への依存は設けない。**完全自前実装**とする。

---

## 2. 決定事項

### 2.1 スコープ

| 項目 | 内容 |
| ------ | ------ |
| 目的 | トイポーカーの**研究・実験**向け環境（本番サービスではない） |
| 対象ゲーム（初期） | **Kuhn Poker（2 人）**, **Leduc Hold'em** |
| 実装順序 | **Kuhn（2 人）→ Leduc** |
| 対象ゲーム（将来拡張候補） | Rhode Island Hold'em, FHP など同系の小規模ポーカー |
| 実装言語 | **Python 3.11+** |
| ライセンス | **MIT** |
| 再現対象論文 | **なし**（独自検証で十分） |
| 可視化 | **テキスト履歴**のみ（Graphviz / TensorBoard 等は不要） |

### 2.2 ゲームルール（標準仕様に準拠）

#### Kuhn Poker（2 人版）

OpenSpiel の `kuhn_poker` と同型の定式化を採用する。**3 人版はスコープ外。**

- プレイヤー数: **2**
- デッキ: J, Q, K の 3 枚
- 配布: 各プレイヤーに 1 枚ずつランダム配布、**残り 1 枚は未使用**（非公開）
- アンティ: 各プレイヤー 1（ポット初期値 2）
- ベットサイズ: **固定 1**
- ラウンド: **1 ベッティングラウンド**
- 行動: **PASS**（チェック / フォールド）、**BET**（ベット / コール）
- 行動順: P0 → P1（P0 が先攻）
- 勝敗: ショーダウン時に K > Q > J。フォールド時は残存プレイヤーが pot 獲得
- 零和: P0 の utility + P1 の utility = 0

#### Leduc Hold'em

- プレイヤー数: **2**
- デッキ: 2 スート × {J, Q, K} = **6 枚**
- アンティ: 各プレイヤー 1
- ベットサイズ: ラウンド 1 は **2**、ラウンド 2 は **4**（固定）
- ラウンド: **2 ベッティングラウンド**
- 勝敗: ペア > ハイカード、同ランク比較

### 2.3 API スタイル

**OpenSpiel 風 API で確定。** OpenSpiel 本体は依存に入れず、インターフェースの考え方のみ踏襲する。

#### 確定 API

| メソッド | 説明 |
| ---------- | ------ |
| `game.new_initial_state()` | 初期状態（アンティ投入後）を返す |
| `state.is_terminal()` | 終局かどうか |
| `state.is_chance_node()` | チャンスノード（カード配布等）かどうか |
| `state.current_player()` | 現在の手番プレイヤー ID |
| `state.legal_actions()` | 合法手のリスト |
| `state.chance_outcomes()` | `[(action, prob), ...]`（チャンスノード時） |
| `state.apply_action(action)` | 次状態を返す（非破壊） |
| `state.returns()` | 各プレイヤーのペイオフ（終局時） |
| `state.action_history()` | テキスト履歴用の行動列 |

#### 使用例

```python
state = game.new_initial_state()
while not state.is_terminal():
    if state.is_chance_node():
        outcomes = state.chance_outcomes()
        action = sample_or_iterate(outcomes)
    else:
        player = state.current_player()
        actions = state.legal_actions()
        action = agent.select_action(state, player, actions)
    state = state.apply_action(action)

returns = state.returns()
history = state.action_history()
```

#### 採用理由

- Phase 2 の CFR でゲーム木・チャンスノード・情報集合を自然に扱える
- OpenSpiel の Kuhn（2 人）定式化と整合しやすい
- Gymnasium 互換は将来拡張（§4）として必要になった場合にラッパー追加

### 2.4 Phase 1 機能要件（ゲームが遊べる状態）

#### A. ゲームエンジン

- [ ] ゲーム状態の明示的表現
- [ ] 合法手の列挙
- [ ] 状態遷移（`apply_action` → 次状態）
- [ ] チャンスノード（カード配布）の処理
- [ ] 終局判定とペイオフ（各プレイヤーの utility）
- [ ] 決定論的シード付き RNG

#### B. エージェント

- [ ] 統一 API: `select_action(state, player, legal_actions) -> action`
- [ ] 組み込みエージェント:
  - **RandomAgent** — 合法手から一様ランダム選択
  - **HumanAgent** — CLI（標準入力）でプレイヤーが着手選択

#### C. 実行・表示

- [ ] 1 ハンド完走（Kuhn / Leduc それぞれ）
- [ ] 複数ハンドのバッチ実行（AI 同士）
- [ ] **人間 vs AI の対戦**（CLI。例: 人間 = P0、相手 = RandomAgent）
- [ ] **テキスト形式のハンド履歴**出力
- [ ] 対戦時に自分のカード・合法手・行動の意味を表示

#### D. 品質

- [ ] 型ヒント
- [ ] 単体テスト（ルール正当性、合法手、ペイオフ）
- [ ] README（インストール、対戦デモの実行方法）

### 2.5 Phase 2 機能要件（CFR + 均衡 AI）

Phase 1 完了後に着手。

#### A. 情報集合・ゲーム木

- [ ] 情報集合 ID の生成
- [ ] ゲーム木 / 情報集合木の列挙

#### B. CFR ソルバー

- [ ] CFR（反復 regret matching）の自前実装
- [ ] 戦略表現: infoset → 行動確率テーブル
- [ ] 学習済み戦略の保存・読み込み

#### C. 均衡 AI・評価

- [ ] CFR 戦略に基づくエージェント
- [ ] Exploitability 計算（Leduc 等、2 人零和）
- [ ] Kuhn の既知 Nash 均衡値との数値比較（検証用）

### 2.6 非機能要件

| 項目 | 目標 |
| ------ | ------ |
| 再現性 | シード固定で同一結果 |
| 性能 | Leduc の全ゲーム木展開が数秒以内（Phase 2 時点） |
| 拡張性 | 新ゲーム追加時、`games/` に追加するだけ |
| 依存関係 | コアは **stdlib + numpy のみ** |

ディレクトリ構成・モジュール設計・型定義・テスト方針の詳細は [technical-requirements.md](./technical-requirements.md) を参照。

---

## 3. 未決定事項

| # | 項目 | 現状 | デフォルト案 |
| --- | ------ | ------ | ------------- |
| 1 | Leduc のベット構造拡張 | 未確認 | **標準（2/4 固定）のみ** |
| 2 | 想定ゲーム規模 | 未確認 | Leduc 全展開で十分 |

---

## 4. 将来拡張（Phase 2 以降）

- MCCFR（サンプリング版 CFR）
- 深層 RL 連携（Gymnasium ラッパー追加）
- 追加ゲーム（Rhode Island 等）
- Web UI（ブラウザ上の対人・観戦）

---

## 5. 受け入れ基準

### Phase 1 完了

1. **Kuhn Poker（2 人）** で 1 ハンドを最初から最後まで実行できる
2. **Leduc Hold'em** で 1 ハンドを最初から最後まで実行できる
3. 合法手列挙・ペイオフ計算が正しい（テストで検証）
4. ランダム AI 同士で複数ハンド実行できる
5. **CLI で人間がランダム AI と 1 ハンド対戦できる**（合法手のみ受理、自分のカードが表示される）
6. テキスト形式でハンド履歴が表示される
7. `pytest` が通る
8. README から 5 分以内にデモ実行可能（AI 同士・人間 vs AI の両方）

### Phase 2 完了

1. Kuhn / Leduc で CFR が収束する
2. 学習済み CFR エージェントが利用できる
3. Kuhn の期待ペイオフが既知 Nash 値と一致（許容誤差内）
4. Leduc で exploitability が十分小さい（≈ 0 に近い）
5. 戦略の保存・読み込みができる

---

## 6. 検証用参照値（Phase 2）

### Kuhn Poker（2 人、OpenSpiel 互換設定）

零和ゲーム（P0 + P1 = 0）。OpenSpiel `kuhn_poker` との一致で検証する。

| プレイヤー | 均衡時の期待ペイオフ（文献値） |
| ----------- | ------------------------------- |
| P0（先攻） | -1/18 ≈ -0.0556 |
| P1（後攻） | +1/18 ≈ +0.0556 |

※ 実装時に OpenSpiel の定式化（アンティ・行動順・PASS/BET 意味）と一致することを確認する。

---

## 7. 変更履歴

| 日付 | 変更内容 |
| ------ | ---------- |
| 2026-06-11 | 初版作成 |
| 2026-06-11 | ユーザー回答を反映。Phase 1/2 分割、API 比較追加、可視化・論文再現の方針確定 |
| 2026-06-11 | API を OpenSpiel 風で確定。Kuhn を 2 人版のみに変更（3 人版はスコープ外） |
| 2026-06-11 | 技術要件定義（technical-requirements.md）を追加し整合 |
| 2026-06-11 | Phase 1 に HumanAgent（CLI 対人対戦）を追加 |
