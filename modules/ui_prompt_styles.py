import gradio as gr

from modules import shared, ui_common, ui_components, styles

styles_edit_symbol = '\U0001f58c\uFE0F'  # 🖌️
styles_materialize_symbol = '\U0001f4cb'  # 📋
styles_copy_symbol = '\U0001f4dd'  # 📝


def select_style(name):
    style = shared.prompt_styles.styles.get(name)
    existing = style is not None
    empty = not name

    prompt = style.prompt if style else gr.update()
    negative_prompt = style.negative_prompt if style else gr.update()

    return prompt, negative_prompt, gr.update(visible=existing), gr.update(visible=not empty)


def save_style(name, prompt, negative_prompt):
    if not name:
        return gr.update(visible=False)

    existing_style = shared.prompt_styles.styles.get(name)
    path = existing_style.path if existing_style is not None else None

    style = styles.PromptStyle(name, prompt, negative_prompt, path)
    shared.prompt_styles.styles[style.name] = style
    shared.prompt_styles.save_styles()

    return gr.update(visible=True)


def delete_style(name):
    if name == "":
        return

    shared.prompt_styles.styles.pop(name, None)
    shared.prompt_styles.save_styles()

    return '', '', ''


def materialize_styles(prompt, negative_prompt, styles):
    prompt = shared.prompt_styles.apply_styles_to_prompt(prompt, styles)
    negative_prompt = shared.prompt_styles.apply_negative_styles_to_prompt(negative_prompt, styles)

    return [gr.Textbox.update(value=prompt), gr.Textbox.update(value=negative_prompt), gr.Dropdown.update(value=[])]


def refresh_styles():
    return gr.update(choices=list(shared.prompt_styles.styles)), gr.update(choices=list(shared.prompt_styles.styles))


class UiPromptStyles:
    def __init__(self, tabname, main_ui_prompt, main_ui_negative_prompt):
        self.tabname = tabname
        self.main_ui_prompt = main_ui_prompt
        self.main_ui_negative_prompt = main_ui_negative_prompt

        with gr.Row(elem_id=f"{tabname}_styles_row"):
            self.dropdown = gr.Dropdown(label="スタイル", show_label=False, elem_id=f"{tabname}_styles", choices=list(shared.prompt_styles.styles), value=[], multiselect=True, tooltip="Styles")
            edit_button = ui_components.ToolButton(value=styles_edit_symbol, elem_id=f"{tabname}_styles_edit_button", tooltip="スタイルを編集")

        with gr.Box(elem_id=f"{tabname}_styles_dialog", elem_classes="popup-dialog") as styles_dialog:
            with gr.Row():
                self.selection = gr.Dropdown(label="スタイル", elem_id=f"{tabname}_styles_edit_select", choices=list(shared.prompt_styles.styles), value=[], allow_custom_value=True, info="スタイルを使うと、プロンプトにカスタムテキストを追加できます。スタイルのテキストで {prompt} トークンを使用すると、スタイルを適用したときにユーザーのプロンプトに置き換えられます。それ以外の場合、スタイルのテキストはプロンプトの末尾に追加されます。")
                ui_common.create_refresh_button([self.dropdown, self.selection], shared.prompt_styles.reload, lambda: {"choices": list(shared.prompt_styles.styles)}, f"refresh_{tabname}_styles")
                self.materialize = ui_components.ToolButton(value=styles_materialize_symbol, elem_id=f"{tabname}_style_apply_dialog", tooltip="メインUIのスタイル選択ドロップダウンから選択したすべてのスタイルをプロンプトに適用します。")
                self.copy = ui_components.ToolButton(value=styles_copy_symbol, elem_id=f"{tabname}_style_copy", tooltip="メインUIプロンプトをスタイルにコピー。")

            with gr.Row():
                self.prompt = gr.Textbox(label="プロンプト", show_label=True, elem_id=f"{tabname}_edit_style_prompt", lines=3, elem_classes=["prompt"])

            with gr.Row():
                self.neg_prompt = gr.Textbox(label="ネガティブプロンプト", show_label=True, elem_id=f"{tabname}_edit_style_neg_prompt", lines=3, elem_classes=["prompt"])

            with gr.Row():
                self.save = gr.Button('保存', variant='primary', elem_id=f'{tabname}_edit_style_save', visible=False)
                self.delete = gr.Button('削除', variant='primary', elem_id=f'{tabname}_edit_style_delete', visible=False)
                self.close = gr.Button('閉じる', variant='secondary', elem_id=f'{tabname}_edit_style_close')

        self.selection.change(
            fn=select_style,
            inputs=[self.selection],
            outputs=[self.prompt, self.neg_prompt, self.delete, self.save],
            show_progress=False,
        )

        self.save.click(
            fn=save_style,
            inputs=[self.selection, self.prompt, self.neg_prompt],
            outputs=[self.delete],
            show_progress=False,
        ).then(refresh_styles, outputs=[self.dropdown, self.selection], show_progress=False)

        self.delete.click(
            fn=delete_style,
            _js='function(name){ if(name == "") return ""; return confirm("スタイルを削除 " + name + "?") ? name : ""; }',
            inputs=[self.selection],
            outputs=[self.selection, self.prompt, self.neg_prompt],
            show_progress=False,
        ).then(refresh_styles, outputs=[self.dropdown, self.selection], show_progress=False)

        self.setup_apply_button(self.materialize)

        self.copy.click(
            fn=lambda p, n: (p, n),
            inputs=[main_ui_prompt, main_ui_negative_prompt],
            outputs=[self.prompt, self.neg_prompt],
            show_progress=False,
        )

        ui_common.setup_dialog(button_show=edit_button, dialog=styles_dialog, button_close=self.close)

    def setup_apply_button(self, button):
        button.click(
            fn=materialize_styles,
            inputs=[self.main_ui_prompt, self.main_ui_negative_prompt, self.dropdown],
            outputs=[self.main_ui_prompt, self.main_ui_negative_prompt, self.dropdown],
            show_progress=False,
        ).then(fn=None, _js="function(){update_"+self.tabname+"_tokens(); closePopup();}", show_progress=False)
