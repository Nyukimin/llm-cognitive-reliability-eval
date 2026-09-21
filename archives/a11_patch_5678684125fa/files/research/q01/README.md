# Q01：既存資産の精査記録

更新日：2026-09-21

ここでは、資産を調べたこと、個別問題を採用したこと、LLMを実測したことを分ける。`data/q01/progress.json` の `completed_assets` は資産・プロトコルの一次精査記録ができたという意味であり、全ケースの検証完了を表さない。

## 現在の判断

| 資産 | 一次精査での判断 | 記録 |
|---|---|---|
| A04 MultiChallenge | ケース供給元候補。個別ラベル・実行条件の受入れは別工程。 | [A04](A04_multichallenge_adoption.md) |
| A06 LongMemEval | cleaned版を候補とし、個別の根拠・ラベルを監査。 | [A06](A06_longmemeval_adoption.md) |
| A09 Sycophancy Eval | 根拠なし異議のB05候補。謝罪と最終事実回答の正誤を分離。 | [A09](A09_sycophancy_eval_adoption.md) |
| A10 Belief-R | 更新・維持の対照設計を条件付きで利用。常識的な補完と形式的な含意が競合する原問題の直接採用は保留。 | [A10](A10_belief_r_adoption.md) |
| A11 FaithEval | 固定文脈のB08/B09/B14候補。公開サンプルの部分一致採点は、そのままの正式採用を見送る。全データ取得・個別ラベル・データ許諾は保留。 | [A11](A11_faitheval_adoption.md) |
| A17 MTRAG-UN | A11の後に精査する優先候補。 | 未作成 |

A04〜A10は各時点の精査記録を引き継いでおり、今回のA11調査で再監査したものではない。A10当時に行った検査と未完了事項は下記のとおり保存する。

正式Full採用ケース0件、正式Short採用ケース0件、対象LLM実行0件。A10の8条件の局所検査はパーサーと形式論理の検査であり、LLMの性能結果ではない。全CSVの取得・ハッシュ確認は未完了と記録した。

## 正本の参照順序

原要求は `docs/requirements/requirements_v0.5.md`、全体設計は `docs/design/stage1_v0.3.md`。これらを今回変更していない。`research/assets_registry_v0.3.md` はStage 1からの資産カードであり、各Q01記録が後から確認した版・権利・適合範囲・保留理由を記す。A10については今回の[A10精査記録](A10_belief_r_adoption.md)と[data/q01/A10_belief_r.json](../../data/q01/A10_belief_r.json)を最新の判断とする。古い資産カードの「候補」を、後続の受入れ完了とは解釈しない。

次はA17 MTRAG-UNの資産精査。その後も、正式Fullに入れる前に、選ぶケースごとの入力・根拠・ラベル・経路・利用条件を検証する。未使用検証、実対話化、日本語化、Short抽出を一段の作業と混同しない。

## A10の再現可能な局所検査

上流固定版の `src/prompts/utils.py` を手元に用意し、次を実行する。

```text
python scripts/q01/check_belief_r_contract.py PATH_TO_UPSTREAM_UTILS_PY
```

検査は原ファイルのGit blobが固定値と一致しなければ停止する。上流ファイルはこのリポジトリへ複製していない。必要なコードを許可された方法で取得したうえで使う。確認済み出力は [A10_local_checks.json](../../data/q01/A10_local_checks.json)。モデル・認証情報・ネットワークは使わず、検査結果をFullの問題得点として扱わない。

## A11の採用判断と局所検査

A11の最新判断は [精査記録](A11_faitheval_adoption.md) と [機械可読記録](../../data/q01/A11_faitheval.json) を参照する。Stage 1資産カードを、データの再配布や正式ケースの採用承認へ読み替えない。

上流固定コミットの `README.md` を取得して、次を実行する。

```text
python scripts/q01/check_faitheval_contract.py PATH_TO_UPSTREAM_README_MD
```

READMEのGit blobを照合し、正規化関数と部分一致の判定式だけを抽出して12条件を検査する。モデル・データセットのロード処理は実行しない。確認結果は [A11_local_checks.json](../../data/q01/A11_local_checks.json)。これは採点コードの局所検査であり、対象LLMの性能試験や全データの監査ではない。形式指定から外れるが意味的に妥当な回答については、形式遵守と意味的正しさを分けて解釈する。
