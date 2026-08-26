import sys
import textwrap
import traceback


exception_records = []


def format_traceback(tb):
    return [[f"{x.filename}, line {x.lineno}, {x.name}", x.line] for x in traceback.extract_tb(tb)]


def format_exception(e, tb):
    return {"exception": str(e), "traceback": format_traceback(tb)}


def get_exceptions():
    try:
        return list(reversed(exception_records))
    except Exception as e:
        return str(e)


def record_exception():
    _, e, tb = sys.exc_info()
    if e is None:
        return

    if exception_records and exception_records[-1] == e:
        return

    exception_records.append(format_exception(e, tb))

    if len(exception_records) > 5:
        exception_records.pop(0)


def report(message: str, *, exc_info: bool = False) -> None:
    """
    Print an error message to stderr, with optional traceback.
    """

    record_exception()

    for line in message.splitlines():
        print("***", line, file=sys.stderr)
    if exc_info:
        print(textwrap.indent(traceback.format_exc(), "    "), file=sys.stderr)
        print("---", file=sys.stderr)


def print_error_explanation(message):
    record_exception()

    lines = message.strip().split("\n")
    max_len = max([len(x) for x in lines])

    print('=' * max_len, file=sys.stderr)
    for line in lines:
        print(line, file=sys.stderr)
    print('=' * max_len, file=sys.stderr)


def display(e: Exception, task, *, full_traceback=False):
    record_exception()

    print(f"{task or 'エラー'}: {type(e).__name__}", file=sys.stderr)
    te = traceback.TracebackException.from_exception(e)
    if full_traceback:
        # include frames leading up to the try-catch block
        te.stack = traceback.StackSummary(traceback.extract_stack()[:-2] + te.stack)
    print(*te.format(), sep="", file=sys.stderr)

    message = str(e)
    if "copying a param with shape torch.Size([640, 1024]) from checkpoint, the shape in current model is torch.Size([640, 768])" in message:
        print_error_explanation("""
この問題の最も考えられる原因は、設定ファイルを指定せずにStable Diffusion 2.0モデルをロードしようとしていることです。
解決方法については、https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features#stable-diffusion-20 を参照してください。
        """)


already_displayed = {}


def display_once(e: Exception, task):
    record_exception()

    if task in already_displayed:
        return

    display(e, task)

    already_displayed[task] = 1


def run(code, task):
    try:
        code()
    except Exception as e:
        display(task, e)


def check_versions():
    from packaging import version
    from modules import shared

    import torch
    import gradio

    expected_torch_version = "2.1.2"
    expected_xformers_version = "0.0.23.post1"
    expected_gradio_version = "3.41.2"

    if version.parse(torch.__version__) < version.parse(expected_torch_version):
        print_error_explanation(f"""
あなたは torch {torch.__version__} を実行しています。
このプログラムは torch {expected_torch_version} で動作することがテストされています。
希望するバージョンを再インストールするには、コマンドラインフラグ --reinstall-torch を使用してください。
これにより、多くの大きなファイルがダウンロードされる可能性があり、
最新バージョンでのトレーニングタブに関する問題の報告もあります。
このチェックを無効にするには、コマンドライン引数 --skip-version-check を使用してください。
        """.strip())

    if shared.xformers_available:
        import xformers

        if version.parse(xformers.__version__) < version.parse(expected_xformers_version):
            print_error_explanation(f"""
あなたは xformers {xformers.__version__} を実行しています。
このプログラムは xformers {expected_xformers_version} で動作することがテストされています。
希望するバージョンを再インストールするには、コマンドラインフラグ --reinstall-xformers を使用してください。

このチェックを無効にするには、--skip-version-check コマンドライン引数を使用してください。
            """.strip())

    if gradio.__version__ != expected_gradio_version:
        print_error_explanation(f"""
あなたは gradio {gradio.__version__} を実行しています。
このプログラムは gradio {expected_gradio_version} で動作することがテストされています。
希望するバージョンを再インストールするには、コマンドラインフラグ --reinstall-gradio を使用してください。

Gradioのバージョンが一致しない理由は次の通りです：
- --skip-install フラグを使用している。
- launch.pyではなくwebui.pyでプログラムを起動している。
- 拡張機能が互換性のないGradioのバージョンをインストールする。

このチェックを無効にするには、--skip-version-check コマンドライン引数を使用してください。
        """.strip())

