# Q01：既存資産の精査記録

更新日：2026-09-21

**A11の配布版との相違は[統合記録](A11_reconciliation.md)で処置済み。旧パッチを適用しない。以下の一次精査記録を保持し、追加の検査・由来情報は統合記録を併読する。**

ここでは、資産を調べたこと、個別問題を採用したこと、LLMを実測したことを分ける。`data/q01/progress.json` の `completed_assets` は資産・プロトコルの一次精査記録ができたという意味であり、全ケースの検証完了を表さない。

## 現在の判断

| 資産 | 一次精査での判断 | 記録 |
|---|---|---|
| A04 MultiChallenge | ケース供給元候補。個別ラベル・実行条件の受入れは別工程。 | [A04](A04_multichallenge_adoption.md) |
| A06 LongMemEval | cleaned版を候補とし、個別の根拠・ラベルを監査。 | [A06](A06_longmemeval_adoption.md) |
| A09 Sycophancy Eval | 根拠なし異議のB05候補。謝罪と最終事実回答の正誤を分離。 | [A09](A09_sycophancy_eval_adoption.md) |
| A10 Belief-R | 更新・維持の対照設計を条件付きで利用。常識的な補完と形式的な含意が競合する原問題の直接採用は保留。 | [A10](A10_belief_r_adoption.md) |
| A11 FaithEval | 固定資料への忠実性の条件付き候補。公開採点例は流用せず、データ権利・全文ラベル監査を保留。 | [A11](A11_faitheval_adoption.md) |
| A17 MTRAG-UN | 指定不足・文脈解決の条件付き候補。回答のみの確認JudgeをB14全体の採点へ流用しない。 | [A17](A17_mtragun_adoption.md) |

上のA04/A06/A09は、既存の記録の状態を引き継いだもので、今回A10の作業で再監査したという意味ではない。

正式Full採用ケース0件、正式Short採用ケース0件、対象LLM実行0件。A10の8条件の局所検査はパーサーと形式論理の検査であり、LLMの性能結果ではない。全CSVの取得・ハッシュ確認は未完了と記録した。

## 正本の参照順序

原要求は `docs/requirements/requirements_v0.5.md`、全体設計は `docs/design/stage1_v0.3.md`。これらを今回変更していない。`research/assets_registry_v0.3.md` はStage 1からの資産カードであり、各Q01記録が後から確認した版・権利・適合範囲・保留理由を記す。A10については今回の[A10精査記録](A10_belief_r_adoption.md)と[data/q01/A10_belief_r.json](../../data/q01/A10_belief_r.json)を最新の判断とする。古い資産カードの「候補」を、後続の受入れ完了とは解釈しない。

優先6資産の一次精査がそろった。次はA04から候補ケースを個別に精査し、正式Fullに入れる前に、選ぶケースごとの入力・根拠・ラベル・経路・利用条件を検証する。未使用検証、実対話化、日本語化、Short抽出を一段の作業と混同しない。

## A10の再現可能な局所検査

上流固定版の `src/prompts/utils.py` を手元に用意し、次を実行する。

```text
python scripts/q01/check_belief_r_contract.py PATH_TO_UPSTREAM_UTILS_PY
```

検査は原ファイルのGit blobが固定値と一致しなければ停止する。上流ファイルはこのリポジトリへ複製していない。必要なコードを許可された方法で取得したうえで使う。確認済み出力は [A10_local_checks.json](../../data/q01/A10_local_checks.json)。モデル・認証情報・ネットワークは使わず、検査結果をFullの問題得点として扱わない。

## A11の追加確認

A11の最新判断は [A11精査記録](A11_faitheval_adoption.md) と [A11機械可読記録](../../data/q01/A11_faitheval.json)。Stage 1の資産カードを過去時点の記録として残し、公開採点例・データ配布条件の今回の確認はQ01記録を参照する。A04〜A10の結論を今回再監査した意味ではない。

```text
python scripts/q01/check_faitheval_contract.py
```

12個の人工応答でREADMEの文字列採点例を検査する独立した等価実装であり、上流コード全文の実行や、被評価モデルの試験ではない。出力は [A11_local_checks.json](../../data/q01/A11_local_checks.json)。形式違反と意味上の誤りを区別し、反例の件数を実データ上の誤判定率とはしない。データセット全文取得・ハッシュ照合・正式な個別採用は未完了。

## A11配布版との統合検査

元のGitHub版と配布版は別の入力例・実装である。原文を残したうえで、[統合記録](A11_reconciliation.md)と[機械可読の対応](../../data/q01/A11_reconciliation.json)へ接続した。`archives/` は原資料の保管で、現在の作業手順・進捗ではない。

```text
python scripts/q01/check_faitheval_reconciliation.py PATH_TO_PINNED_UPSTREAM_README_MD
```

固定READMEのGit blob、両実装、配布版6ファイルを照合してから、元の各12入力の結果と、両版の全入力に対する判定を比較する。[実行結果](../../data/q01/A11_reconciliation_checks.json)は24出所付きエントリ、22種類の課題・応答組、2モード48比較。不一致0。これらを独立したLLM試行数として数えない。

今後の反映報告では、作業開始時のmain、生成したファイルのhash、検査結果、書込み結果、最後に再取得したmainを区別する。書込み経路が使えないことをリモート未反映の証拠にせず、後の存在確認から過去の操作主体を推定しない。これらは運用条件であり、再発しないことの実証ではない。

## A17の追加確認と次工程

最新判断は [A17精査記録](A17_mtragun_adoption.md) と [A17機械可読記録](../../data/q01/A17_mtragun.json)。論文記載666件を取得・採用済み件数にせず、公開予定領域と未集計を区別する。

```text
python scripts/q01/check_mtragun_contract.py PATH_TO_PINNED_UNDERSPECIFIED_EVAL_PY
```

固定版の整形関数を抽出実行し、質問と資料が異なる3対で同じ回答が同じJudge入力になることを確認した。[局所検査結果](../../data/q01/A17_local_checks.json)は入力の欠落を検査したもので、Judgeの誤判定率や対象モデル性能ではない。

A04/A06/A09/A10/A11/A17の一次精査済みは、Q01全要件の完了ではない。次はA04の候補から個別の入力・ラベル・権利・正常対照を具体化する。Q02のB02/B03/B06/B07/B11不足も維持し、Fullに必要な未測定領域を落とさない。
