# mkdocs-heti-plugin

一个使用 [heti](https://github.com/sivan/heti) 来优化 mkdocs 中文正文排版的插件。

具体表现在：

- 中西文混排间使用四分宽空格
    - 注：与 heti 不同，此时复制得到的是带半角空格的文本，而 heti 原脚本复制下来不带空格
- 进行连续标点的挤压

预览：https://note.tonycrane.cc/

## 提示
heti 原本是跑在前端的，不过在加载出页面到 heti 处理好之间有一小段时间间隔，感觉有些不爽，就写了这个插件，将这个任务直接放到网站生成的时候来做。

不过嘛，效率是极低的，我的 note 用上之后需要三分多钟才能完成网站构建。

如果可以忍受在前端处理的话可以看这个 commit：[TonyCrane/note@`5a0259`](https://github.com/TonyCrane/note/commit/5a02592e23bbf756ab02e4452f83eab80d694768)

## 安装
可以通过 pypi 直接安装：
```shell
$ pip install mkdocs-heti-plugin
```

也可以从源码安装

```shell
$ git clone https://github.com/TonyCrane/mkdocs-heti-plugin.git
$ cd mkdocs-heti-plugin
$ pip install . # or pip install -e .
```

## 使用
- 在 mkdocs.yml 中启用插件即可：
    ```yaml
    plugins:
      - heti
    ```
- 由于效率实在是太低，所以默认在 serve 的时候不进行处理，想要处理的话这样写：
    ```yaml
    plugins:
      - heti:
          disable_serve: false
    ```
- 使用 pymdownx.arithmatex 的数学公式的话会提前加入空格会导致公式不渲染，所以需要忽略掉其生成的 .arithmatex 类：
    ```yaml
    plugins:
      - heti:
          extra_skipped_class:
            - arithmatex
    ```
    - 但这样的话，数学公式左右的空格并不会进行处理
    - 不过使用 js 的 heti 的话也是无法处理的，先放一放

目前配置项配置的不多，用法啥的也以后再完善（~~咕咕咕~~

## 开发
`mkdocs_heti_plugin/utils/finder.py` 是我对着 [padolsey/findAndReplaceDOMText](https://github.com/padolsey/findAndReplaceDOMText) 的 js 代码扒出来的，我也不敢说我看懂了，反正它目前确实能跑，能用就行了。

`mkdocs_heti_plugin/utils/heti.py` 里面有一些用很不优雅的方式解决的一些不想深究的 bug，有时间再细看看。

有想修改、改进的我非常且热烈欢迎，尽管 PR 就好（

### TODO
- [ ] 与 mkdocs-encryptcontent-plugin 加密页面兼容
- [ ] 支持 pymdownx.arithmatex

## 注意事项
与 mkdocs-encryptcontent-plugin 还没兼容，加密的页面目前不做处理（处理的话目前会卡死）。

## 参考 & 鸣谢
- [sivan/heti](https://github.com/sivan/heti)
- [padolsey/findAndReplaceDOMText](https://github.com/padolsey/findAndReplaceDOMText)