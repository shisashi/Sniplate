# Sniplate for Sublime Text 3
## これは何?

競技プログラミングに特化した snipet 挿入プログラム [sniplate.vim](https://github.com/MiSawa/sniplate.vim) の Sublime Text 3 プラグイン版です。

sniplate の機能については、[紹介記事](http://d.hatena.ne.jp/Mi_Sawa/20130212) を参照してください。

## INSTALL

Sublime Text 3 のプラグイン管理ディレクトリに、このプロジェクト内のファイルを置くだけでインストールできます。

例えば MacOS 版の場合は以下のコマンドを実行してください。

```
git clone https://github.com/shisashi/Sniplate ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/Sniplate
```

Windows と Linux は知りませんが、それっぽいディレクトリがあるはずなので、そこに置けば実行できると思います。

## 使い方
### sniplate を選んで挿入する

command pallete で `List Sniplates.` を実行するか、ショートカット `super+shift+s` を押してください。
quick panel が表示され、選んだ snipet と、その依存 snipet がカーソル位置に挿入されます。

### sniplate を選んで編集する

command pallete で `Edit Sniplates.` を実行するか、ショートカット `super+shift+e` を押してください。
選んだ snipet が定義されているファイルを開きます。

## sniplate.vim との違い

### 割と高速

sniplate.vim より軽快に動作します。

### sniplate の動的読み込みができる

snipet を定義したファイルを編集して保存すると、即座にその内容が反映されます。

### snipet が挿入済みかどうかの判定方法
snipet を挿入すると、その先頭に独自のコメント行を付与して、それで判定を行っています。
例えば、C++ にて `hoge` という snipet を挿入すると、

```cpp
// sniplate: hoge
// ここに hoge という snipet の内容が入る
```

が挿入されます。
私は、submit 用にプログラムをコピーするときは、[submit するテキストを clipboard にコピーするプラグイン](https://gist.github.com/shisashi/d31a241e73ac1f3d5c0413a0b288db23) を使っています。
これを使えば、この行は除去されるため、このような仕様となっています。

### 一部のキーワードにしか対応していない

- require, invisible, priority, var

対応済みです

- class, abbr

指定された値が command palette に表示されますが、この値を使った絞り込みはできません（そのうち対応するつもりです）

- cursor

未対応です（そのうち対応するつもりです）

- pattern

pattern の値は無視されます。pattern の用途としては、前述の通り、コメント行が使われます。

- eval, exec, let, input

未対応です。
任意のvimコマンドを snipet 挿入時に実行する命令ですが、Sublime Text 3 では互換性がなくなるので、どうしようか考慮中です。
私がこの機能を使っていないため、サポートに対するモチベーションは低いです。

# 言い訳
このプログラムは自分だけが使う用のプログラムとして開発が開始されたもので、公開を意図していませんでした。
ですので、若干やっつけ気味のコードがあります。

# LICENSE
Copyright (c) 2017 S.Hisashi

Released under the MIT license
https://github.com/shisashi/Sniplate/blob/master/MIT-LICENSE.txt
