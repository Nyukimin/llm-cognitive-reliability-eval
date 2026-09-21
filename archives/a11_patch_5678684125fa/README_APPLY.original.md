# A11 FaithEval精査一式：Git未反映の適用用パッケージ

作成日：2026-09-21
対象：Nyukimin/llm-cognitive-reliability-eval
確認したmain：90289d4b4a44dabc19621c99a82dcef3c4fcca0d

## 状態

A11の一次精査、4レコードの表示確認（全文表示2件・省略あり2件）、README採点サンプルの12条件の局所実行を行った。
今回はGitHub読取操作は利用できたが、更新操作が公開されていなかったため、リモートへcommit・pushしていない。
このZIP内のprogress.jsonは**適用後の案**であり、GitHubの更新済み状態ではない。確認時のGitHub正本はA10まで。

含まれるものは6個の変更ファイル、Gitパッチ、変更ファイルのハッシュ一覧、ローカル検査記録。このZIPはリポジトリ全体のバックアップではない。
要求仕様v0.5、Stage 1設計、A04〜A10の個別記録、原データ・私的ログは変更・複製していない。

## 内容を確認する

- files/research/q01/A11_faitheval_adoption.md：採用候補・保留理由・出典
- files/data/q01/A11_faitheval.json：機械可読の資産記録
- files/data/q01/A11_local_checks.json：12条件の実行結果
- files/scripts/q01/check_faitheval_contract.py：再検査用コード
- files/data/q01/progress.json、files/research/q01/README.md：進捗・索引の限定更新案

## 適用

既存リポジトリのローカル作業ツリーで実施する。既存の未コミット変更を破棄しない。ZIPからのファイルコピーとGitパッチの両方を重ねて行わず、原則パッチを使う。

```text
git status --short
git rev-parse HEAD
git apply --check /path/to/A11_FaithEval_Q01.patch
git apply /path/to/A11_FaithEval_Q01.patch
git diff --check
git status --short
```

パッチは上記mainの2ファイルと一致する内容に対して確認した。HEADが進んでいる場合は差分を確認し、--checkが失敗したら上書き・強制適用しない。
追加した4ファイルは未追跡として表示される。内容確認後、今回の6ファイルだけを指定してcommitする。

```text
git add data/q01/A11_faitheval.json data/q01/A11_local_checks.json data/q01/progress.json research/q01/A11_faitheval_adoption.md research/q01/README.md scripts/q01/check_faitheval_contract.py
git diff --cached --stat
git commit -m "Record FaithEval source and scorer audit for Q01"
git push origin HEAD
```

push先ブランチは作業中のブランチを維持する。この資料がpush成功を報告するものではない。

## 検査の意味

適用元2ファイルはGitHubのGit blobと一致することを確認した。ローカルの小さなベース作業ツリーで `git apply --check`、適用後6ファイルのバイト一致、再適用の拒否を確認した。リポジトリ全体のテストやGitHub CIを実行したという意味ではない。

採点プローブは固定READMEの正規化関数と部分一致式だけを実行する。必要な上流READMEは利用条件を確認して別途取得する。モデル・認証情報・ネットワークは使わない。実データ全件、正式採点、人手評価の検証は未実施。
