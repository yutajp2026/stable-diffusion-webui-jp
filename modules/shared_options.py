import os
import gradio as gr

from modules import localization, ui_components, shared_items, shared, interrogate, shared_gradio_themes, util, sd_emphasis
from modules.paths_internal import models_path, script_path, data_path, sd_configs_path, sd_default_config, sd_model_file, default_sd_model_file, extensions_dir, extensions_builtin_dir, default_output_dir  # noqa: F401
from modules.shared_cmd_options import cmd_opts
from modules.options import options_section, OptionInfo, OptionHTML, categories

options_templates = {}
hide_dirs = shared.hide_dirs

restricted_opts = {
    "samples_filename_pattern",
    "directories_filename_pattern",
    "outdir_samples",
    "outdir_txt2img_samples",
    "outdir_img2img_samples",
    "outdir_extras_samples",
    "outdir_grids",
    "outdir_txt2img_grids",
    "outdir_save",
    "outdir_init_images",
    "temp_dir",
    "clean_temp_dir_at_start",
}

categories.register_category("saving", "画像を保存する")
categories.register_category("sd", "Stable Diffusion")
categories.register_category("ui", "ユーザーインターフェース")
categories.register_category("system", "システム")
categories.register_category("postprocessing", "後処理")
categories.register_category("training", "トレーニング")

options_templates.update(options_section(('saving-images', "画像/グリッドを保存", "saving"), {
    "samples_save": OptionInfo(True, "生成されたすべての画像を常に保存する"),
    "samples_format": OptionInfo('png', '画像のファイル形式'),
    "samples_filename_pattern": OptionInfo("", "画像ファイル名のパターン", component_args=hide_dirs).link("wiki", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory"),
    "save_images_add_number": OptionInfo(True, "保存時にファイル名に番号を追加", component_args=hide_dirs),
    "save_images_replace_action": OptionInfo("Replace", "既存ファイルへの保存時の動作", gr.Radio, {"choices": ["Replace", "Add number suffix"], **hide_dirs}),
    "grid_save": OptionInfo(True, "生成された画像グリッドを常に保存する"),
    "grid_format": OptionInfo('png', 'グリッドのファイル形式'),
    "grid_extended_filename": OptionInfo(False, "グリッド保存時に詳細情報（シード、プロンプト）をファイル名に追加"),
    "grid_only_if_multiple": OptionInfo(True, "1枚だけのグリッドは保存しない"),
    "grid_prevent_empty_spots": OptionInfo(False, "グリッドの空きスペースを防ぐ（自動判定時）"),
    "grid_zip_filename_pattern": OptionInfo("", "アーカイブのファイル名パターン", component_args=hide_dirs).link("wiki", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory"),
    "n_rows": OptionInfo(-1, "グリッドの行数；自動判定は -1、バッチサイズと同じにするには 0", gr.Slider, {"minimum": -1, "maximum": 16, "step": 1}),
    "font": OptionInfo("", "テキスト付き画像グリッドのフォント"),
    "grid_text_active_color": OptionInfo("#000000", "画像グリッドの文字色", ui_components.FormColorPicker, {}),
    "grid_text_inactive_color": OptionInfo("#999999", "画像グリッドの非アクティブ文字色", ui_components.FormColorPicker, {}),
    "grid_background_color": OptionInfo("#ffffff", "画像グリッドの背景色", ui_components.FormColorPicker, {}),

    "save_images_before_face_restoration": OptionInfo(False, "顔修復の前に画像のコピーを保存する。"),
    "save_images_before_highres_fix": OptionInfo(False, "ハイレゾ修正の前に画像のコピーを保存する。"),
    "save_images_before_color_correction": OptionInfo(False, "img2img 結果に色補正を適用する前に画像のコピーを保存する"),
    "save_mask": OptionInfo(False, "インペイント時にグレースケールマスクのコピーを保存"),
    "save_mask_composite": OptionInfo(False, "インペイント時にマスク付き合成画像を保存"),
    "jpeg_quality": OptionInfo(80, "保存した jpeg / avif 画像の品質", gr.Slider, {"minimum": 1, "maximum": 100, "step": 1}),
    "webp_lossless": OptionInfo(False, "webp 画像に無損失圧縮を使用"),
    "export_for_4chan": OptionInfo(True, "大きい画像を JPG としてコピー保存").info("ファイルサイズや幅/高さが上限を超えた場合"),
    "img_downscale_threshold": OptionInfo(4.0, "上記オプションのファイルサイズ制限、MB", gr.Number),
    "target_side_length": OptionInfo(4000, "上記オプションの幅/高さ制限、ピクセル", gr.Number),
    "img_max_size_mp": OptionInfo(200, "最大画像サイズ", gr.Number).info("メガピクセル"),

    "use_original_name_batch": OptionInfo(True, "Extras タブのバッチ処理時に元の名前を出力ファイル名に使用"),
    "use_upscaler_name_as_suffix": OptionInfo(False, "Extras タブでアップスケーラ名をファイル名の接尾辞として使用"),
    "save_selected_only": OptionInfo(True, "『保存』ボタン使用時、選択中の画像を 1 枚だけ保存"),
    "save_write_log_csv": OptionInfo(True, "『保存』ボタンで画像を保存する際に log.csv を書き出す"),
    "save_init_img": OptionInfo(False, "img2img 使用時に初期画像を保存"),

    "temp_dir":  OptionInfo("", "一時画像のディレクトリ；空欄ならデフォルトを使用"),
    "clean_temp_dir_at_start": OptionInfo(False, "WebUI 起動時にデフォルト以外の一時ディレクトリを削除"),

    "save_incomplete_images": OptionInfo(False, "途中生成の画像を保存").info("途中で中断された画像を保存する；保存されなくても WebUI の出力には表示される"),

    "notification_audio": OptionInfo(True, "画像生成後に通知音を再生").info("notification.mp3 がルートディレクトリに存在する必要があります").needs_reload_ui(),
    "notification_volume": OptionInfo(100, "通知音の音量", gr.Slider, {"minimum": 0, "maximum": 100, "step": 1}).info("%"),
}))

options_templates.update(options_section(('saving-paths', "保存先のパス", "saving"), {
    "outdir_samples": OptionInfo("", "画像の出力ディレクトリ；空欄なら以下の 3 つを使用", component_args=hide_dirs),
    "outdir_txt2img_samples": OptionInfo(util.truncate_path(os.path.join(default_output_dir, 'txt2img-images')), 'txt2img 画像の出力ディレクトリ', component_args=hide_dirs),
    "outdir_img2img_samples": OptionInfo(util.truncate_path(os.path.join(default_output_dir, 'img2img-images')), 'img2img 画像の出力ディレクトリ', component_args=hide_dirs),
    "outdir_extras_samples": OptionInfo(util.truncate_path(os.path.join(default_output_dir, 'extras-images')), 'Extras タブの画像出力ディレクトリ', component_args=hide_dirs),
    "outdir_grids": OptionInfo("", "グリッドの出力ディレクトリ；空欄なら以下の 2 つを使用", component_args=hide_dirs),
    "outdir_txt2img_grids": OptionInfo(util.truncate_path(os.path.join(default_output_dir, 'txt2img-grids')), 'txt2img グリッドの出力ディレクトリ', component_args=hide_dirs),
    "outdir_img2img_grids": OptionInfo(util.truncate_path(os.path.join(default_output_dir, 'img2img-grids')), 'img2img グリッドの出力ディレクトリ', component_args=hide_dirs),
    "outdir_save": OptionInfo(util.truncate_path(os.path.join(data_path, 'log', 'images')), "『保存』ボタンで画像を保存するディレクトリ", component_args=hide_dirs),
    "outdir_init_images": OptionInfo(util.truncate_path(os.path.join(default_output_dir, 'init-images')), "img2img 使用時の初期画像保存ディレクトリ", component_args=hide_dirs),
}))

options_templates.update(options_section(('saving-to-dirs', "ディレクトリへ保存", "saving"), {
    "save_to_dirs": OptionInfo(True, "サブディレクトリに画像を保存"),
    "grid_save_to_dirs": OptionInfo(True, "サブディレクトリにグリッドを保存"),
    "use_save_to_dirs_for_ui": OptionInfo(False, "『保存』ボタン使用時にサブディレクトリへ保存"),
    "directories_filename_pattern": OptionInfo("[date]", "ディレクトリ名のパターン", component_args=hide_dirs).link("wiki", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory"),
    "directories_max_prompt_words": OptionInfo(8, "[prompt_words] パターンの最大プロンプト単語数", gr.Slider, {"minimum": 1, "maximum": 20, "step": 1, **hide_dirs}),
}))

options_templates.update(options_section(('upscaling', "アップスケーリング", "postprocessing"), {
    "ESRGAN_tile": OptionInfo(192, "ESRGAN アップスケーラのタイルサイズ。", gr.Slider, {"minimum": 0, "maximum": 512, "step": 16}).info("0 = タイルなし"),
    "ESRGAN_tile_overlap": OptionInfo(8, "ESRGAN アップスケーラのタイル重なり。", gr.Slider, {"minimum": 0, "maximum": 48, "step": 1}).info("小さい値 = 目立つ継ぎ目"),
    "realesrgan_enabled_models": OptionInfo(["R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B"], "Web UI に表示する Real-ESRGAN モデルを選択。", gr.CheckboxGroup, lambda: {"choices": shared_items.realesrgan_models_names()}),
    "dat_enabled_models": OptionInfo(["DAT x2", "DAT x3", "DAT x4"], "Web UI に表示する DAT モデルを選択。", gr.CheckboxGroup, lambda: {"choices": shared_items.dat_models_names()}),
    "DAT_tile": OptionInfo(192, "DAT アップスケーラのタイルサイズ。", gr.Slider, {"minimum": 0, "maximum": 512, "step": 16}).info("0 = タイルなし"),
    "DAT_tile_overlap": OptionInfo(8, "DAT アップスケーラのタイル重なり。", gr.Slider, {"minimum": 0, "maximum": 48, "step": 1}).info("小さい値 = 目立つ継ぎ目"),
    "upscaler_for_img2img": OptionInfo(None, "img2img 用アップスケーラ", gr.Dropdown, lambda: {"choices": [x.name for x in shared.sd_upscalers]}),
    "set_scale_by_when_changing_upscaler": OptionInfo(False, "選択中のアップスケーラ名に基づいて拡大率を自動的に設定。"),
}))

options_templates.update(options_section(('face-restoration', "顔修復", "postprocessing"), {
    "face_restoration": OptionInfo(False, "顔を修復", infotext='Face restoration').info("生成結果にサードパーティ製モデルを使って顔を再構築します"),
    "face_restoration_model": OptionInfo("CodeFormer", "顔修復モデル", gr.Radio, lambda: {"choices": [x.name() for x in shared.face_restorers]}),
    "code_former_weight": OptionInfo(0.5, "CodeFormer の重み", gr.Slider, {"minimum": 0, "maximum": 1, "step": 0.01}).info("0 = 最大効果; 1 = 最小効果"),
    "face_restoration_unload": OptionInfo(False, "処理後に顔修復モデルを VRAM から RAM に移す"),
}))

options_templates.update(options_section(('system', "システム", "system"), {
    "auto_launch_browser": OptionInfo("Local", "起動時に WebUI をブラウザで自動的に開く", gr.Radio, lambda: {"choices": ["Disable", "Local", "Remote"]}),
    "enable_console_prompts": OptionInfo(shared.cmd_opts.enable_console_prompts, "txt2img と img2img 生成時にプロンプトをコンソールに出力."),
    "show_warnings": OptionInfo(False, "コンソールに警告を表示.").needs_reload_ui(),
    "show_gradio_deprecation_warnings": OptionInfo(True, "コンソールに Gradio の非推奨警告を表示.").needs_reload_ui(),
    "memmon_poll_rate": OptionInfo(8, "生成中の VRAM 使用量を 1 秒あたり何回確認するか.", gr.Slider, {"minimum": 0, "maximum": 40, "step": 1}).info("0 = 無効"),
    "samples_log_stdout": OptionInfo(False, "すべての生成情報を標準出力に常に表示"),
    "multiple_tqdm": OptionInfo(True, "ジョブ全体の進捗を示す 2 つ目の進捗バーをコンソールに追加."),
    "enable_upscale_progressbar": OptionInfo(True, "タイル状のアップスケーリングの進捗バーをコンソールに表示."),
    "print_hypernet_extra": OptionInfo(False, "ハイパーネットワークの追加情報をコンソールに出力."),
    "list_hidden_files": OptionInfo(True, "隠しディレクトリ内のモデル/ファイルを読み込む").info("ディレクトリ名が \".\" で始まる場合は隠し扱い"),
    "disable_mmap_load_safetensors": OptionInfo(False, ".safetensors ファイルの読み込みで memmapping を無効化.").info("場合によっては読み込み速度が非常に遅くなる問題を修正"),
    "hide_ldm_prints": OptionInfo(True, "Stability-AI の ldm/sgm モジュールがノイズをコンソールに出力しないようにする."),
    "dump_stacks_on_signal": OptionInfo(False, "ctrl+c で終了する直前にスタックトレースを出力."),
}))

options_templates.update(options_section(('profiler', "プロファイラ", "system"), {
    "profiling_explanation": OptionHTML("""
これらの設定により、画像生成時に torch プロファイラを有効にできます。
プロファイリングにより、生成中にどのコードがどれだけコンピュータのリソースを使用しているかを確認できます。
各生成はそれぞれ独自のプロファイルを 1 ファイルに書き込み、前のものを上書きします。
このファイルは <a href="chrome:tracing">Chrome</a> や <a href="https://ui.perfetto.dev/">Perfetto</a> で閲覧できます。
注意: プロファイルの書き込みには最大 30 秒ほどかかり、ファイルサイズは約 500MB になることがあります。
"""),
    "profiling_enable": OptionInfo(False, "プロファイリングを有効化"),
    "profiling_activities": OptionInfo(["CPU"], "アクティビティ", gr.CheckboxGroup, {"choices": ["CPU", "CUDA"]}),
    "profiling_record_shapes": OptionInfo(True, "形状を記録"),
    "profiling_profile_memory": OptionInfo(True, "メモリをプロファイル"),
    "profiling_with_stack": OptionInfo(True, "Python スタックを含める"),
    "profiling_filename": OptionInfo("trace.json", "プロファイルのファイル名"),
}))

options_templates.update(options_section(('API', "API", "system"), {
    "api_enable_requests": OptionInfo(True, "API で入力画像として http:// と https:// URL を許可", restrict_api=True),
    "api_forbid_local_requests": OptionInfo(True, "ローカルリソースへの URL を禁止", restrict_api=True),
    "api_useragent": OptionInfo("", "リクエスト時の User agent", restrict_api=True),
}))

options_templates.update(options_section(('training', "トレーニング", "training"), {
    "unload_models_when_training": OptionInfo(False, "可能なら学習時に VAE と CLIP を RAM に移す。VRAM を節約。"),
    "pin_memory": OptionInfo(False, "DataLoader に pin_memory を有効化。学習がやや高速になるがメモリ使用量が増える可能性がある。"),
    "save_optimizer_state": OptionInfo(False, "Optimizer 状態を別の *.optim ファイルとして保存。対応する optim ファイルで embedding や HN の学習を再開できる。"),
    "save_training_settings_to_txt": OptionInfo(True, "学習開始時に Textual Inversion と Hypernetwork の設定をテキストファイルとして保存。"),
    "dataset_filename_word_regex": OptionInfo("", "ファイル名の単語正規表現"),
    "dataset_filename_join_string": OptionInfo(" ", "ファイル名の連結文字列"),
    "training_image_repeats_per_epoch": OptionInfo(1, "1 枚の入力画像を 1 エポックあたり何回繰り返すか；エポック番号表示のみに使用", gr.Number, {"precision": 0}),
    "training_write_csv_every": OptionInfo(500, "N ステップごとに損失を含む CSV をログディレクトリへ保存、0 で無効"),
    "training_xattention_optimizations": OptionInfo(False, "学習中に cross attention 最適化を使用"),
    "training_enable_tensorboard": OptionInfo(False, "TensorBoard ログを有効化."),
    "training_tensorboard_save_images": OptionInfo(False, "TensorBoard 内に生成画像を保存."),
    "training_tensorboard_flush_every": OptionInfo(120, "保留中の TensorBoard イベントと要約をディスクへ書き出す間隔（秒）。"),
}))

options_templates.update(options_section(('sd', "Stable Diffusion", "sd"), {
    "sd_model_checkpoint": OptionInfo(None, "Stable Diffusion チェックポイント", gr.Dropdown, lambda: {"choices": shared_items.list_checkpoint_tiles(shared.opts.sd_checkpoint_dropdown_use_short)}, refresh=shared_items.refresh_checkpoints, infotext='Model hash'),
    "sd_checkpoints_limit": OptionInfo(1, "同時に読み込むチェックポイントの最大数", gr.Slider, {"minimum": 1, "maximum": 10, "step": 1}),
    "sd_checkpoints_keep_in_cpu": OptionInfo(True, "デバイス上にモデルを 1 つだけ保持").info("現在使用中のモデル以外は VRAM ではなく RAM に保持"),
    "sd_checkpoint_cache": OptionInfo(0, "RAM にキャッシュするチェックポイント数", gr.Slider, {"minimum": 0, "maximum": 10, "step": 1}).info("非推奨; 0 にして上の 2 つの設定を使用"),
    "sd_unet": OptionInfo("Automatic", "SD Unet", gr.Dropdown, lambda: {"choices": shared_items.sd_unet_items()}, refresh=shared_items.refresh_unet_list).info("Unet モデルを選択: Automatic = チェックポイントと同じファイル名のものを使用; None = チェックポイント内の Unet を使用"),
    "enable_quantization": OptionInfo(False, "K サンプラーで量子化を有効にして、より鮮明できれいな結果を得る。既存のシードが変わる可能性があります").needs_reload_ui(),
    "emphasis": OptionInfo("Original", "Emphasis モード", gr.Radio, lambda: {"choices": [x.name for x in sd_emphasis.options]}, infotext="Emphasis").info("プロンプト構文使用時にモデルがテキストに注目する度合いを調整できます（より多く:1.1 / より少なく:0.9）; " + sd_emphasis.get_options_descriptions()),
    "enable_batch_seeds": OptionInfo(True, "K-diffusion サンプラーで、単一画像生成時とバッチ生成時で同じ画像が得られるようにする"),
    "comma_padding_backtrack": OptionInfo(20, "プロンプトの改行長制限", gr.Slider, {"minimum": 0, "maximum": 74, "step": 1}).info("トークン数 - 指定値より短いテキストは 75 token 制限に収まらない場合、次の 75 token ブロックへ移動"),
    "sdxl_clip_l_skip": OptionInfo(False, "SDXL の Clip skip", gr.Checkbox).info("sdxl のセカンダリ CLIP モデルで Clip skip を有効化。SD 1.5 や SD 2.0/2.1 には影響しません。"),
    "CLIP_stop_at_last_layers": OptionInfo(1, "Clip skip", gr.Slider, {"minimum": 1, "maximum": 12, "step": 1}, infotext="Clip skip").link("wiki", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features#clip-skip").info("CLIP ネットワークの最終層を無視; 1 = 無視なし, 2 = 1 層無視"),
    "upcast_attn": OptionInfo(False, "クロスアテンション層を float32 にアップキャスト"),
    "randn_source": OptionInfo("GPU", "乱数生成器のソース。", gr.Radio, {"choices": ["GPU", "CPU", "NV"]}, infotext="RNG").info("シードが大きく変わります; CPU を使うと異なるビデオカード間でも同じ画像を生成できます; NV を使うと NVIDIA ビデオカードと同じ画像になります"),
    "tiling": OptionInfo(False, "タイリング", infotext='Tiling').info("タイル可能な画像を生成"),
    "hires_fix_refiner_pass": OptionInfo("second pass", "Hires fix: リファイナーを有効にするパス", gr.Radio, {"choices": ["first pass", "second pass", "both passes"]}, infotext="Hires refiner"),
}))

options_templates.update(options_section(('sdxl', "Stable Diffusion XL", "sd"), {
    "sdxl_crop_top": OptionInfo(0, "上部の crop 座標"),
    "sdxl_crop_left": OptionInfo(0, "左側の crop 座標"),
    "sdxl_refiner_low_aesthetic_score": OptionInfo(2.5, "SDXL 低美術評価値", gr.Number).info("リファイナーモデルの negative prompt に使用"),
    "sdxl_refiner_high_aesthetic_score": OptionInfo(6.0, "SDXL 高美術評価値", gr.Number).info("リファイナーモデルの prompt に使用"),
}))

options_templates.update(options_section(('sd3', "Stable Diffusion 3", "sd"), {
    "sd3_enable_t5": OptionInfo(False, "T5 を有効化").info("T5 テキストエンコーダを読み込む; VRAM 使用量が大幅に増える可能性があり、生成品質が改善する場合がある; 反映にはモデル再読込が必要"),
}))

options_templates.update(options_section(('vae', "VAE", "sd"), {
    "sd_vae_explanation": OptionHTML("""
<abbr title='Variational autoencoder'>VAE</abbr> は、標準的な <abbr title='red/green/blue'>RGB</abbr> 画像を潜在空間表現に変換して戻すニューラルネットワークです。
潜在空間表現は、サンプリング中に Stable Diffusion が扱う空間です。
（進捗バーが空から満杯の間の状態）。txt2img では、サンプリング終了後に VAE を使って最終画像を生成します。
img2img では、サンプリング前にユーザー入力画像を処理し、サンプリング後に画像を生成するために VAE を使います。
"""),
    "sd_vae_checkpoint_cache": OptionInfo(0, "RAM にキャッシュする VAE チェックポイント数", gr.Slider, {"minimum": 0, "maximum": 10, "step": 1}),
    "sd_vae": OptionInfo("Automatic", "SD VAE", gr.Dropdown, lambda: {"choices": shared_items.sd_vae_items()}, refresh=shared_items.refresh_vae_list, infotext='VAE').info("VAE モデルを選択: Automatic = チェックポイントと同じファイル名のものを使用; None = チェックポイント内の VAE を使用"),
    "sd_vae_overrides_per_model_preferences": OptionInfo(True, "選択した VAE がモデルごとの設定を上書き").info("チェックポイントのユーザーメタデータを編集するか、VAE の名前をチェックポイントと同じにすると、モデルごとに VAE を設定できます"),
    "auto_vae_precision_bfloat16": OptionInfo(False, "VAE を自動的に bfloat16 に変換").info("VAE 内で NaN を含むテンソルが生成されたときに発動; この場合に無効にすると黒い四角画像になり、有効にすると下の設定を上書き"),
    "auto_vae_precision": OptionInfo(True, "VAE を自動的に 32 ビット浮動小数点へ戻す").info("VAE 内で NaN を含むテンソルが生成されたときに発動; この場合に無効にすると黒い四角画像になる"),
    "sd_vae_encode_method": OptionInfo("Full", "エンコード用 VAE の種類", gr.Radio, {"choices": ["Full", "TAESD"]}, infotext='VAE Encoder').info("画像を潜在表現へエンコードする方法（img2img、hires-fix、inpaint mask で使用）"),
    "sd_vae_decode_method": OptionInfo("Full", "デコード用 VAE の種類", gr.Radio, {"choices": ["Full", "TAESD"]}, infotext='VAE Decoder').info("潜在表現を画像へデコードする方法"),
}))

options_templates.update(options_section(('img2img', "img2img", "sd"), {
    "inpainting_mask_weight": OptionInfo(1.0, "インペイント時の条件マスク強度", gr.Slider, {"minimum": 0.0, "maximum": 1.0, "step": 0.01}, infotext='Conditional mask weight'),
    "initial_noise_multiplier": OptionInfo(1.0, "img2img のノイズ倍率", gr.Slider, {"minimum": 0.0, "maximum": 1.5, "step": 0.001}, infotext='Noise multiplier'),
    "img2img_extra_noise": OptionInfo(0.0, "img2img と hires fix の追加ノイズ倍率", gr.Slider, {"minimum": 0.0, "maximum": 1.0, "step": 0.01}, infotext='Extra noise').info("0 = 無効（デフォルト）; denoising strength より低くする必要がある"),
    "img2img_color_correction": OptionInfo(False, "元画像の色に合わせるために img2img 結果に色補正を適用"),
    "img2img_fix_steps": OptionInfo(False, "img2img ではスライダーで指定したステップ数をそのまま実行").info("通常は denoising が少ない場合は少ないステップ数で処理する"),
    "img2img_background_color": OptionInfo("#ffffff", "img2img で入力画像の透明部分をこの色で埋める。", ui_components.FormColorPicker, {}),
    "img2img_editor_height": OptionInfo(720, "画像エディターの高さ", gr.Slider, {"minimum": 80, "maximum": 1600, "step": 1}).info("ピクセル").needs_reload_ui(),
    "img2img_sketch_default_brush_color": OptionInfo("#ffffff", "スケッチの初期ブラシ色", ui_components.FormColorPicker, {}).info("img2img スケッチのデフォルトブラシ色").needs_reload_ui(),
    "img2img_inpaint_mask_brush_color": OptionInfo("#ffffff", "インペイントマスクのブラシ色", ui_components.FormColorPicker,  {}).info("インペイントマスクのブラシ色").needs_reload_ui(),
    "img2img_inpaint_sketch_default_brush_color": OptionInfo("#ffffff", "インペイントスケッチの初期ブラシ色", ui_components.FormColorPicker, {}).info("img2img インペイントスケッチのデフォルトブラシ色").needs_reload_ui(),
    "return_mask": OptionInfo(False, "インペイント時に Web 用にグレースケールマスクを結果に含める"),
    "return_mask_composite": OptionInfo(False, "インペイント時に Web 用にマスク合成画像を結果に含める"),
    "img2img_batch_show_results_limit": OptionInfo(32, "UI に表示するバッチ img2img 結果の先頭 N 枚", gr.Slider, {"minimum": -1, "maximum": 1000, "step": 1}).info('0: 無効, -1: すべての画像を表示. 画像が多すぎると遅くなることがある'),
    "overlay_inpaint": OptionInfo(True, "インペイント時に元画像をオーバーレイ").info("インペイント時、修復しなかった領域に元画像を重ねます。"),
}))

options_templates.update(options_section(('optimizations', "最適化", "sd"), {
    "cross_attention_optimization": OptionInfo("Automatic", "Cross attention 最適化", gr.Dropdown, lambda: {"choices": shared_items.cross_attention_optimizations()}),
    "s_min_uncond": OptionInfo(0.0, "Negative Guidance 最小 sigma", gr.Slider, {"minimum": 0.0, "maximum": 15.0, "step": 0.01}, infotext='NGMS').link("PR", "https://github.com/AUTOMATIC1111/stablediffusion-webui/pull/9177").info("画像がほぼ完成した時点で一部のステップで negative prompt を省略; 0=無効, 高いほど高速"),
    "s_min_uncond_all": OptionInfo(False, "Negative Guidance 最小 sigma を全ステップで適用", infotext='NGMS all steps').info("デフォルトでは NGMS は毎回ではなくステップを飛ばします; この設定で全ステップを飛ばします"),
    "token_merging_ratio": OptionInfo(0.0, "Token merging 比率", gr.Slider, {"minimum": 0.0, "maximum": 0.9, "step": 0.1}, infotext='Token merging ratio').link("PR", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/9256").info("0=無効, 高いほど高速"),
    "token_merging_ratio_img2img": OptionInfo(0.0, "img2img 用 Token merging 比率", gr.Slider, {"minimum": 0.0, "maximum": 0.9, "step": 0.1}).info("0 以外の場合のみ適用され、上記を上書き"),
    "token_merging_ratio_hr": OptionInfo(0.0, "ハイレゾパス用 Token merging 比率", gr.Slider, {"minimum": 0.0, "maximum": 0.9, "step": 0.1}, infotext='Token merging ratio hr').info("0 以外の場合のみ適用され、上記を上書き"),
    "pad_cond_uncond": OptionInfo(False, "prompt/negative prompt を埋める", infotext='Pad conds').info("prompt と negative prompt の長さが異なる場合にパフォーマンスが改善; シードが変わる"),
    "pad_cond_uncond_v0": OptionInfo(False, "prompt/negative prompt を埋める (v0)", infotext='Pad conds v0').info("上記の代替実装; 1.6.0 より前に DDIM サンプラーで使用; 設定時は上記を上書き; 警告: negative prompt が長すぎると切り詰められる; シードが変わる"),
    "persistent_cond_cache": OptionInfo(True, "条件キャッシュを保持").info("前回計算時から prompt が変わっていない場合、cond を再計算しない"),
    "batch_cond_uncond": OptionInfo(True, "バッチ cond/uncond").info("1 バッチ内で条件付き・無条件の両方を同時に処理; サンプリング中に VRAM を少し多く使うが高速化; 以前は --always-batch-cond-uncond コマンドライン引数で制御されていた"),
    "fp8_storage": OptionInfo("Disable", "FP8 重み", gr.Radio, {"choices": ["Disable", "Enable for SDXL", "Enable"]}).info("Linear/Conv 層の重みを FP8 で保存。pytorch>=2.1.0 が必要。"),
    "cache_fp16_weight": OptionInfo(False, "LoRA の FP16 重みをキャッシュ").info("FP8 を有効化したとき FP16 重みをキャッシュし、LoRA の品質を向上させる。システム RAM を増やす。"),
}))

options_templates.update(options_section(('compatibility', "互換性", "sd"), {
    "auto_backcompat": OptionInfo(True, "自動後方互換性").info("プログラムのバージョン情報を含む infotext から生成パラメータを読み込むとき、後方互換のためのオプションを自動的に有効化"),
    "use_old_emphasis_implementation": OptionInfo(False, "古い emphasis 実装を使用。古いシードを再現するときに役立つことがある。"),
    "use_old_karras_scheduler_sigmas": OptionInfo(False, "古い karras scheduler sigmas を使用 (0.1 to 10)。"),
    "no_dpmpp_sde_batch_determinism": OptionInfo(False, "DPM++ SDE をバッチサイズが異なっても決定的にしない。"),
    "use_old_hires_fix_width_height": OptionInfo(False, "hires fix で、最初のパスではなく幅/高さスライダーを最終解像度として使う（Upscale by, Resize width/height to を無効化）。"),
    "hires_fix_use_firstpass_conds": OptionInfo(False, "hires fix で、2 番目のパスの cond を最初のパスの extra networks で計算する。"),
    "use_old_scheduling": OptionInfo(False, "古いプロンプト編集タイムラインを使用。", infotext="Old prompt editing timelines").info("[red:green:N] の場合; 古い方式: N < 1 ならステップの割合（hires fix は 0 to 1 の範囲を使用）、N >= 1 なら絶対ステップ数; 新方式: N に小数点が含まれるならステップの割合（hires fix は 1 to 2 の範囲を使用）、それ以外は絶対ステップ数"),
    "use_downcasted_alpha_bar": OptionInfo(False, "サンプリング前にモデルの alphas_cumprod を fp16 にダウンキャスト。古いシード再現用。", infotext="Downcast alphas_cumprod"),
    "refiner_switch_by_sample_steps": OptionInfo(False, "モデル timestep ではなくサンプリングステップで refiner を切り替える。古い refiner の挙動。", infotext="Refiner switch by sampling steps")
}))

options_templates.update(options_section(('interrogate', "Interrogate"), {
    "interrogate_keep_models_in_memory": OptionInfo(False, "VRAM にモデルを保持"),
    "interrogate_return_ranks": OptionInfo(False, "結果にモデルタグ一致のランクを含める").info("booru のみ"),
    "interrogate_clip_num_beams": OptionInfo(1, "BLIP: num_beams", gr.Slider, {"minimum": 1, "maximum": 16, "step": 1}),
    "interrogate_clip_min_length": OptionInfo(24, "BLIP: 最小説明長", gr.Slider, {"minimum": 1, "maximum": 128, "step": 1}),
    "interrogate_clip_max_length": OptionInfo(48, "BLIP: 最大説明長", gr.Slider, {"minimum": 1, "maximum": 256, "step": 1}),
    "interrogate_clip_dict_limit": OptionInfo(1500, "CLIP: テキストファイルの最大行数").info("0 = 無制限"),
    "interrogate_clip_skip_categories": OptionInfo([], "CLIP: 問い合わせカテゴリをスキップ", gr.CheckboxGroup, lambda: {"choices": interrogate.category_types()}, refresh=interrogate.category_types),
    "interrogate_deepbooru_score_threshold": OptionInfo(0.5, "deepbooru: スコア閾値", gr.Slider, {"minimum": 0, "maximum": 1, "step": 0.01}),
    "deepbooru_sort_alpha": OptionInfo(True, "deepbooru: タグをアルファベット順に並べる").info("無効時: スコア順に並べる"),
    "deepbooru_use_spaces": OptionInfo(True, "deepbooru: タグにスペースを使用").info("無効時: アンダースコアを使用"),
    "deepbooru_escape": OptionInfo(True, "deepbooru: 括弧をエスケープ (\\)").info("リテラル括弧として使うためで、emphasis には使わない"),
    "deepbooru_filter_tags": OptionInfo("", "deepbooru: これらのタグを除外").info("カンマ区切り"),
}))

options_templates.update(options_section(('extra_networks', "Extra Networks", "sd"), {
    "extra_networks_show_hidden_directories": OptionInfo(True, "隠しディレクトリを表示").info("ディレクトリ名が \".\" で始まる場合は隠し扱い"),
    "extra_networks_dir_button_function": OptionInfo(False, "ディレクトリボタンの先頭に '/' を追加").info("ボタンは検索フィルターとしてではなく、選択したディレクトリの内容を表示します。"),
    "extra_networks_hidden_models": OptionInfo("When searched", "隠しディレクトリ内のモデルカードを表示", gr.Radio, {"choices": ["Always", "When searched", "Never"]}).info('"When searched" オプションは検索文字列が 4 文字以上のときのみ項目を表示します'),
    "extra_networks_default_multiplier": OptionInfo(1.0, "Extra Networks のデフォルト倍率", gr.Slider, {"minimum": 0.0, "maximum": 2.0, "step": 0.01}),
    "extra_networks_card_width": OptionInfo(0, "Extra Networks カードの幅").info("ピクセル"),
    "extra_networks_card_height": OptionInfo(0, "Extra Networks カードの高さ").info("ピクセル"),
    "extra_networks_card_text_scale": OptionInfo(1.0, "カード文字サイズ", gr.Slider, {"minimum": 0.0, "maximum": 2.0, "step": 0.01}).info("1 = 元のサイズ"),
    "extra_networks_card_show_desc": OptionInfo(True, "カードに説明を表示"),
    "extra_networks_card_description_is_html": OptionInfo(False, "カード説明を HTML として扱う"),
    "extra_networks_card_order_field": OptionInfo("Path", "Extra Networks カードの既定並び順項目", gr.Dropdown, {"choices": ['Path', 'Name', 'Date Created', 'Date Modified']}).needs_reload_ui(),
    "extra_networks_card_order": OptionInfo("Ascending", "Extra Networks カードの既定順序", gr.Dropdown, {"choices": ['Ascending', 'Descending']}).needs_reload_ui(),
    "extra_networks_tree_view_style": OptionInfo("Dirs", "Extra Networks ディレクトリ表示スタイル", gr.Radio, {"choices": ["Tree", "Dirs"]}).needs_reload_ui(),
    "extra_networks_tree_view_default_enabled": OptionInfo(True, "デフォルトで Extra Networks ディレクトリ表示を表示").needs_reload_ui(),
    "extra_networks_tree_view_default_width": OptionInfo(180, "Extra Networks ディレクトリツリーの既定幅", gr.Number).needs_reload_ui(),
    "extra_networks_add_text_separator": OptionInfo(" ", "Extra networks 区切り文字").info("prompt に extra network を追加するとき <...> の前に入れる追加テキスト"),
    "ui_extra_networks_tab_reorder": OptionInfo("", "Extra networks タブの順序").needs_reload_ui(),
    "textual_inversion_print_at_load": OptionInfo(False, "モデル読込時に Textual Inversion embedding の一覧を出力"),
    "textual_inversion_add_hashes_to_infotext": OptionInfo(True, "infotext に Textual Inversion ハッシュを追加"),
    "sd_hypernetwork": OptionInfo("None", "prompt に hypernetwork を追加", gr.Dropdown, lambda: {"choices": ["None", *shared.hypernetworks]}, refresh=shared_items.reload_hypernetworks),
}))

options_templates.update(options_section(('ui_prompt_editing', "プロンプト編集", "ui"), {
    "keyedit_precision_attention": OptionInfo(0.1, "Ctrl+↑/↓ でプロンプトを編集するときの (attention:1.1) の精度", gr.Slider, {"minimum": 0.01, "maximum": 0.2, "step": 0.001}),
    "keyedit_precision_extra": OptionInfo(0.05, "Ctrl+↑/↓ でプロンプトを編集するときの <extra networks:0.9> の精度", gr.Slider, {"minimum": 0.01, "maximum": 0.2, "step": 0.001}),
    "keyedit_delimiters": OptionInfo(r".,\/!?%^*;:{}=`~() ", "Ctrl+↑/↓ でプロンプトを編集するときの単語区切り文字"),
    "keyedit_delimiters_whitespace": OptionInfo(["Tab", "Carriage Return", "Line Feed"], "Ctrl+↑/↓ での空白区切り文字", gr.CheckboxGroup, lambda: {"choices": ["Tab", "Carriage Return", "Line Feed"]}),
    "keyedit_move": OptionInfo(True, "Alt+←/→ でプロンプト要素を移動"),
    "disable_token_counters": OptionInfo(False, "プロンプト token カウンターを無効化"),
    "include_styles_into_token_counters": OptionInfo(True, "有効なスタイルのトークンも数える").info("プロンプトのトークン数を計算する際、有効なスタイルによって追加されたトークンも考慮する。"),
}))

options_templates.update(options_section(('ui_gallery', "ギャラリー", "ui"), {
    "return_grid": OptionInfo(True, "ギャラリーにグリッドを表示"),
    "do_not_show_images": OptionInfo(False, "ギャラリーに画像を表示しない"),
    "js_modal_lightbox": OptionInfo(True, "フルページ画像ビューア: 有効"),
    "js_modal_lightbox_initially_zoomed": OptionInfo(True, "フルページ画像ビューア: デフォルトで拡大表示"),
    "js_modal_lightbox_gamepad": OptionInfo(False, "フルページ画像ビューア: ゲームパッドで移動"),
    "js_modal_lightbox_gamepad_repeat": OptionInfo(250, "フルページ画像ビューア: ゲームパッドのリピート期間").info("ミリ秒"),
    "sd_webui_modal_lightbox_icon_opacity": OptionInfo(1, "フルページ画像ビューア: コントロールアイコンの非フォーカス時の透明度", gr.Slider, {"minimum": 0.0, "maximum": 1, "step": 0.01}, onchange=shared.reload_gradio_theme).info('マウス専用').needs_reload_ui(),
    "sd_webui_modal_lightbox_toolbar_opacity": OptionInfo(0.9, "フルページ画像ビューア: ツールバーの透明度", gr.Slider, {"minimum": 0.0, "maximum": 1, "step": 0.01}, onchange=shared.reload_gradio_theme).info('マウス専用').needs_reload_ui(),
    "gallery_height": OptionInfo("", "ギャラリーの高さ", gr.Textbox).info("768px や 20em など、CSS で有効な値なら何でも可").needs_reload_ui(),
    "open_dir_button_choice": OptionInfo("Subdirectory", "[📂] ボタンが開くディレクトリ", gr.Radio, {"choices": ["Output Root", "Subdirectory", "Subdirectory (even temp dir)"]}),
}))

options_templates.update(options_section(('ui_alternatives', "UI の代替案", "ui"), {
    "compact_prompt_box": OptionInfo(False, "プロンプトレイアウトをコンパクト化").info("Generate タブ内に prompt と negative prompt を配置し、右側の画像用により多くの縦スペースを確保").needs_reload_ui(),
    "samplers_in_dropdown": OptionInfo(True, "サンプラー選択をラジオグループではなくドロップダウンで使用").needs_reload_ui(),
    "dimensions_and_batch_together": OptionInfo(True, "幅/高さとバッチスライダーを同じ行に表示").needs_reload_ui(),
    "sd_checkpoint_dropdown_use_short": OptionInfo(False, "チェックポイントドロップダウン: パスなしのファイル名を使用").info("photo/sd15.ckpt のようなサブディレクトリのモデルは sd15.ckpt のみ表示されます"),
    "hires_fix_show_sampler": OptionInfo(False, "Hires fix: hires チェックポイントとサンプラー選択を表示").needs_reload_ui(),
    "hires_fix_show_prompts": OptionInfo(False, "Hires fix: hires prompt と negative prompt を表示").needs_reload_ui(),
    "txt2img_settings_accordion": OptionInfo(False, "txt2img の設定をアコーディオンで隠す").needs_reload_ui(),
    "img2img_settings_accordion": OptionInfo(False, "img2img の設定をアコーディオンで隠す").needs_reload_ui(),
    "interrupt_after_current": OptionInfo(True, "途中で中断しない").info("Interrupt ボタン使用時、複数画像生成中なら 1 枚生成が終わった後で停止し、すぐには中断しない"),
}))

options_templates.update(options_section(('ui', "ユーザーインターフェース", "ui"), {
    "localization": OptionInfo("None", "ローカライズ", gr.Dropdown, lambda: {"choices": ["None"] + list(localization.localizations.keys())}, refresh=lambda: localization.list_localizations(cmd_opts.localizations_dir)).needs_reload_ui(),
    "quicksettings_list": OptionInfo(["sd_model_checkpoint"], "クイック設定一覧", ui_components.DropdownMulti, lambda: {"choices": list(shared.opts.data_labels.keys())}).js("info", "settingsHintsShowQuicksettings").info("ページ上部に表示される設定項目").needs_reload_ui(),
    "ui_tab_order": OptionInfo([], "UI タブの順序", ui_components.DropdownMulti, lambda: {"choices": list(shared.tab_names)}).needs_reload_ui(),
    "hidden_tabs": OptionInfo([], "非表示 UI タブ", ui_components.DropdownMulti, lambda: {"choices": list(shared.tab_names)}).needs_reload_ui(),
    "ui_reorder_list": OptionInfo([], "txt2img/img2img タブの UI 項目順", ui_components.DropdownMulti, lambda: {"choices": list(shared_items.ui_reorder_categories())}).info("選択項目が先に表示されます").needs_reload_ui(),
    "gradio_theme": OptionInfo("Default", "Gradio テーマ", ui_components.DropdownEditable, lambda: {"choices": ["Default"] + shared_gradio_themes.gradio_hf_hub_themes}).info("<a href='https://huggingface.co/spaces/gradio/theme-gallery'>gallery</a> のテーマを手動で入力することもできます。").needs_reload_ui(),
    "gradio_themes_cache": OptionInfo(True, "Gradio テーマをローカルにキャッシュ").info("無効にすると選択中の Gradio テーマを更新"),
    "show_progress_in_title": OptionInfo(True, "ウィンドウタイトルに生成進捗を表示."),
    "send_seed": OptionInfo(True, "プロンプトや画像を他のインターフェイスへ送るときシードも送信"),
    "send_size": OptionInfo(True, "プロンプトや画像を他のインターフェイスへ送るときサイズも送信"),
    "enable_reloading_ui_scripts": OptionInfo(False, "Reload UI オプション使用時に UI スクリプトを再読込").info("開発に便利: UI スクリプトコードを変更した場合、UI を再読込すると反映されます。"),

}))


options_templates.update(options_section(('infotext', "Infotext", "ui"), {
    "infotext_explanation": OptionHTML("""
Infotext とは、このソフトウェアが生成パラメータを含むテキストとして扱うものを指し、同じ画像を再生成するときに使えます。
UI 上では画像の下に表示されます。Infotext を使うには、プロンプトに貼り付けて ↙️ ペーストボタンを押します。
"""),
    "enable_pnginfo": OptionInfo(True, "生成画像のメタデータに infotext を書き込む"),
    "save_txt": OptionInfo(False, "生成された画像ごとに infotext を含むテキストファイルを作成"),

    "add_model_name_to_info": OptionInfo(True, "infotext にモデル名を追加"),
    "add_model_hash_to_info": OptionInfo(True, "infotext にモデルハッシュを追加"),
    "add_vae_name_to_info": OptionInfo(True, "infotext に VAE 名を追加"),
    "add_vae_hash_to_info": OptionInfo(True, "infotext に VAE ハッシュを追加"),
    "add_user_name_to_info": OptionInfo(False, "認証済みの場合に infotext にユーザー名を追加"),
    "add_version_to_infotext": OptionInfo(True, "infotext にプログラムバージョンを追加"),
    "disable_weights_auto_swap": OptionInfo(True, "貼り付けた infotext のチェックポイント情報を無視").info("UI に生成パラメータを読み込むとき"),
    "infotext_skip_pasting": OptionInfo([], "貼り付けた infotext から無視する項目", ui_components.DropdownMulti, lambda: {"choices": shared_items.get_infotext_names()}),
    "infotext_styles": OptionInfo("Apply if any", "貼り付けた infotext のプロンプトからスタイルを推測", gr.Radio, {"choices": ["Ignore", "Apply", "Discard", "Apply if any"]}).info("UI に生成パラメータを読み込むとき").html("""<ul style='margin-left: 1.5em'>
<li>Ignore: prompt と styles ドロップダウンはそのままにする。</li>
<li>Apply: prompt からスタイルテキストを削除し、発見したスタイルがあれば styles ドロップダウンの値を常に置き換える（見つからなくても置き換える）。</li>
<li>Discard: prompt からスタイルテキストを削除し、styles ドロップダウンはそのままにする。</li>
<li>Apply if any: prompt からスタイルテキストを削除し、プロンプト中にスタイルが見つかれば styles ドロップダウンへ入れ、見つからなければそのままにする。</li>
</ul>"""),

}))

options_templates.update(options_section(('ui', "ライブプレビュー", "ui"), {
    "show_progressbar": OptionInfo(True, "進捗バーを表示"),
    "live_previews_enable": OptionInfo(True, "生成中の画像のライブプレビューを表示"),
    "live_previews_image_format": OptionInfo("png", "ライブプレビューのファイル形式", gr.Radio, {"choices": ["jpeg", "png", "webp"]}),
    "show_progress_grid": OptionInfo(True, "バッチで生成されたすべての画像のプレビューをグリッドで表示"),
    "show_progress_every_n_steps": OptionInfo(10, "ライブプレビュー表示の間隔", gr.Slider, {"minimum": -1, "maximum": 32, "step": 1}).info("サンプリングステップ数 - N ステップごとに新しいライブプレビュー画像を表示; -1 = バッチ完了後のみ表示"),
    "show_progress_type": OptionInfo("Approx NN", "ライブプレビュー方式", gr.Radio, {"choices": ["Full", "Approx NN", "Approx cheap", "TAESD"]}).info("Full = 遅いがきれい; Approx NN と TAESD = 速いが低品質; Approx cheap = 非常に速いがひどく低品質"),
    "live_preview_allow_lowvram_full": OptionInfo(False, "lowvram/medvram でも Full ライブプレビューを許可").info("無効時は Approx NN が使われます; Full ライブプレビューは lowvram/medvram 最適化時に速度が著しく低下します"),
    "live_preview_content": OptionInfo("Prompt", "ライブプレビューの対象", gr.Radio, {"choices": ["Combined", "Prompt", "Negative prompt"]}),
    "live_preview_refresh_period": OptionInfo(1000, "進捗バーとプレビューの更新間隔").info("ミリ秒"),
    "live_preview_fast_interrupt": OptionInfo(False, "中断時に選択したライブプレビュー方式の画像を返す").info("中断を高速化"),
    "js_live_preview_in_modal_lightbox": OptionInfo(False, "フルページ画像ビューアでライブプレビューを表示"),
    "prevent_screen_sleep_during_generation": OptionInfo(True, "生成中に画面のスリープを防ぐ"),
}))

options_templates.update(options_section(('sampler-params', "サンプラー設定", "sd"), {
    "hide_samplers": OptionInfo([], "ユーザーインターフェースでサンプラーを隠す", gr.CheckboxGroup, lambda: {"choices": [x.name for x in shared_items.list_samplers()]}).needs_reload_ui(),
    "eta_ddim": OptionInfo(0.0, "DDIM の Eta", gr.Slider, {"minimum": 0.0, "maximum": 1.0, "step": 0.01}, infotext='Eta DDIM').info("ノイズ倍率; 高いほど予測不能な結果になる"),
    "eta_ancestral": OptionInfo(1.0, "k-diffusion サンプラーの Eta", gr.Slider, {"minimum": 0.0, "maximum": 1.0, "step": 0.01}, infotext='Eta').info("ノイズ倍率; 現在 ancestral サンプラー（例: Euler a）と SDE サンプラーにのみ適用"),
    "ddim_discretize": OptionInfo('uniform', "img2img DDIM の離散化", gr.Radio, {"choices": ['uniform', 'quad']}),
    's_churn': OptionInfo(0.0, "sigma churn", gr.Slider, {"minimum": 0.0, "maximum": 100.0, "step": 0.01}, infotext='Sigma churn').info('確率性の量; Euler, Heun, DPM2 のみ適用'),
    's_tmin':  OptionInfo(0.0, "sigma tmin",  gr.Slider, {"minimum": 0.0, "maximum": 10.0, "step": 0.01}, infotext='Sigma tmin').info('確率性を有効化; sigma 範囲の開始値; Euler, Heun, DPM2 のみ適用'),
    's_tmax':  OptionInfo(0.0, "sigma tmax",  gr.Slider, {"minimum": 0.0, "maximum": 999.0, "step": 0.01}, infotext='Sigma tmax').info("0 = inf; sigma 範囲の終了値; Euler, Heun, DPM2 のみ適用"),
    's_noise': OptionInfo(1.0, "sigma noise", gr.Slider, {"minimum": 0.0, "maximum": 1.1, "step": 0.001}, infotext='Sigma noise').info('サンプリング中のディテール損失に対抗する追加ノイズ量'),
    'sigma_min': OptionInfo(0.0, "sigma min", gr.Number, infotext='Schedule min sigma').info("0 = デフォルト (~0.03); k-diffusion ノイズスケジューラの最小ノイズ強度"),
    'sigma_max': OptionInfo(0.0, "sigma max", gr.Number, infotext='Schedule max sigma').info("0 = デフォルト (~14.6); k-diffusion ノイズスケジューラの最大ノイズ強度"),
    'rho':  OptionInfo(0.0, "rho", gr.Number, infotext='Schedule rho').info("0 = デフォルト (karras では 7, polyexponential では 1); 大きいほどノイズスケジュールが急になる（より早く減少）"),
    'eta_noise_seed_delta': OptionInfo(0, "Eta noise seed delta", gr.Number, {"precision": 0}, infotext='ENSD').info("ENSD; 何の改善にもならず、ancestral サンプラーで異なる結果を生むだけ - 画像再現にのみ役立つ"),
    'always_discard_next_to_last_sigma': OptionInfo(False, "最後から 2 番目の sigma を常に破棄", infotext='Discard penultimate sigma').link("PR", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/6044"),
    'sgm_noise_multiplier': OptionInfo(False, "SGM noise multiplier", infotext='SGM noise multiplier').link("PR", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/12818").info("公式 SDXL 実装に初期ノイズを合わせる - 画像再現にのみ有用"),
    'uni_pc_variant': OptionInfo("bh1", "UniPC バリアント", gr.Radio, {"choices": ["bh1", "bh2", "vary_coeff"]}, infotext='UniPC variant'),
    'uni_pc_skip_type': OptionInfo("time_uniform", "UniPC skip type", gr.Radio, {"choices": ["time_uniform", "time_quadratic", "logSNR"]}, infotext='UniPC skip type'),
    'uni_pc_order': OptionInfo(3, "UniPC order", gr.Slider, {"minimum": 1, "maximum": 50, "step": 1}, infotext='UniPC order').info("サンプリングステップより小さくする必要あり"),
    'uni_pc_lower_order_final': OptionInfo(True, "UniPC lower order final", infotext='UniPC lower order final'),
    'sd_noise_schedule': OptionInfo("Default", "サンプリング用ノイズスケジュール", gr.Radio, {"choices": ["Default", "Zero Terminal SNR"]}, infotext="Noise Schedule").info("zero terminal SNR で学習したモデル向け"),
    'skip_early_cond': OptionInfo(0.0, "初期サンプリング中に negative prompt を無視", gr.Slider, {"minimum": 0.0, "maximum": 1.0, "step": 0.01}, infotext="Skip Early CFG").info("生成開始時の一部ステップで CFG を無効化; 0=無視なし; 1=全て無視; サンプルの多様性/品質向上や高速化に寄与することがある"),
    'beta_dist_alpha': OptionInfo(0.6, "Beta scheduler - alpha", gr.Slider, {"minimum": 0.01, "maximum": 1.0, "step": 0.01}, infotext='Beta scheduler alpha').info('デフォルト = 0.6; Beta sampling で使われる beta 分布の alpha パラメータ'),
    'beta_dist_beta': OptionInfo(0.6, "Beta scheduler - beta", gr.Slider, {"minimum": 0.01, "maximum": 1.0, "step": 0.01}, infotext='Beta scheduler beta').info('デフォルト = 0.6; Beta sampling で使われる beta 分布の beta パラメータ'),
}))

options_templates.update(options_section(('postprocessing', "後処理", "postprocessing"), {
    'postprocessing_enable_in_main_ui': OptionInfo([], "txt2img と img2img タブで後処理を有効化", ui_components.DropdownMulti, lambda: {"choices": [x.name for x in shared_items.postprocessing_scripts()]}),
    'postprocessing_disable_in_extras': OptionInfo([], "Extras タブで後処理を無効化", ui_components.DropdownMulti, lambda: {"choices": [x.name for x in shared_items.postprocessing_scripts()]}),
    'postprocessing_operation_order': OptionInfo([], "後処理の実行順序", ui_components.DropdownMulti, lambda: {"choices": [x.name for x in shared_items.postprocessing_scripts()]}),
    'upscaling_max_images_in_cache': OptionInfo(5, "アップスケーリングキャッシュ内の最大画像数", gr.Slider, {"minimum": 0, "maximum": 10, "step": 1}),
    'postprocessing_existing_caption_action': OptionInfo("Ignore", "既存キャプションへの動作", gr.Radio, {"choices": ["Ignore", "Keep", "Prepend", "Append"]}).info("後処理でキャプション生成時; Ignore = 生成したものを使う; Keep = 元のものを使う; Prepend/Append = 両方を組み合わせる"),
}))

options_templates.update(options_section((None, "非表示オプション"), {
    "disabled_extensions": OptionInfo([], "これらの拡張機能を無効化"),
    "disable_all_extensions": OptionInfo("none", "すべての拡張機能を無効化（無効化リストは保持）", gr.Radio, {"choices": ["none", "extra", "all"]}),
    "restore_config_state_file": OptionInfo("", "config-states/ 配下から復元する設定状態ファイル"),
    "sd_checkpoint_hash": OptionInfo("", "現在のチェックポイントの SHA256 ハッシュ"),
}))
